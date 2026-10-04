"""Run the shared-name review checks using explicit built executables."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET


def validate_core_report(path):
    """Reject missing, incomplete or failing core-test reports."""
    try:
        root = ET.parse(path).getroot()
        cases = list(root.iter("testcase"))
        new_cases = []
        edit_cases = []
        registered_cases = []
        for suite in root.iter("testsuite"):
            is_new_suite = suite.get("name") == "IDUINameTest"
            if is_new_suite:
                new_cases.extend(suite.findall("testcase"))
            is_edit_suite = suite.get("name") == "IDNameEditTest"
            if is_edit_suite:
                edit_cases.extend(suite.findall("testcase"))
            is_registered_suite = suite.get("name") == "RegisteredNodeToolDisplayNameTest"
            if is_registered_suite:
                registered_cases.extend(suite.findall("testcase"))
        has_expected_cases = (len(cases) >= 77 and len(new_cases) >= 30
                              and len(edit_cases) >= 7 and len(registered_cases) >= 3)
        has_filelist_case = any(case.get("name") == "ExternalFileListColdAndWarmTranslatedSearch"
                                for case in registered_cases)
        has_failure = any(case.find("failure") is not None or case.find("error") is not None
                          or case.find("skipped") is not None or case.get("status") == "notrun"
                          for case in cases)
        return has_expected_cases and has_filelist_case and not has_failure
    except (OSError, ET.ParseError):
        return False


def run_check(name, command, artifacts, timeout, core_report=None):
    """Run one check, preserving its output and failure evidence."""
    log_path = artifacts / f"{name}.log"
    env = os.environ.copy()
    for suffix in ("CONFIG", "DATAFILES", "SCRIPTS", "EXTENSIONS"):
        directory = artifacts / "user" / name / suffix.lower()
        directory.mkdir(parents=True)
        env[f"BLENDER_USER_{suffix}"] = str(directory)
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log:
        log.write("Arguments: " + json.dumps(command) + "\n")
        log.flush()
        try:
            result = subprocess.run(command, cwd=Path(__file__).resolve().parents[5],
                                    env=env, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=timeout, check=False)
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\nFAILED: exceeded {timeout} seconds.\n")
            returncode = 124
        except OSError as error:
            log.write(f"\nFAILED: {error}\n")
            returncode = 127
        has_core_report = core_report is not None
        has_valid_report = not has_core_report or (returncode == 0 and validate_core_report(core_report))
        passed = returncode == 0 and has_valid_report
        if not has_valid_report:
            log.write("\nFAILED: expected 77 passing C++ cases, including 30 shared-name, "
                      "7 editing and 3 registered-tool/external cases, including the actual FileList case.\n")
    print(f"{'PASS' if passed else 'FAIL'} {name}: {log_path}", flush=True)
    return {"name": name, "returncode": returncode, "passed": passed,
            "seconds": round(time.monotonic() - started, 3), "log": str(log_path),
            "command": command}


def main():
    """Collect nine checks in a fresh directory and return a reliable review result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--gtest", required=True, type=Path)
    parser.add_argument("--release-dir", type=Path,
                        help="Built Blender version's resource directory, e.g. Resources/5.3")
    parser.add_argument("--output-dir", type=Path,
                        help="Parent directory for a new run-* folder (default: temporary directory)")
    parser.add_argument("--timeout", type=float, default=300,
                        help="Maximum seconds for each check")
    args = parser.parse_args()
    has_valid_inputs = args.blender.is_file() and args.gtest.is_file() and args.timeout > 0
    if not has_valid_inputs:
        parser.error("Provide existing Blender/test executables and a positive timeout.")
    has_output_directory = args.output_dir is not None
    if has_output_directory:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = Path(tempfile.mkdtemp(prefix="run-", dir=args.output_dir)).resolve()
    root = Path(__file__).resolve().parents[5]
    version = Path(__file__).resolve().parents[1]
    report = artifacts / "core.xml"
    core_command = [str(args.gtest.resolve()),
                    "--gtest_filter=IDUINameTest.*:LibID*.*:AssetMetadataTest.*:AssetRepresentationTest.*:OperatorDisplayNameTest.*:RegisteredNodeToolDisplayNameTest.*:IDNameEditTest.*",
                    f"--gtest_output=xml:{report}", f"--test-assets-dir={root / 'tests/files'}"]
    has_release_directory = args.release_dir is not None
    if has_release_directory:
        core_command.append(f"--test-release-dir={args.release_dir.resolve()}")
    blender_command = [str(args.blender.resolve()), "--background", "--factory-startup",
                       "--python-exit-code", "1"]
    scripts = (
        ("python-api", root / "tests/python/bl_id_ui_name.py"),
        ("libraries", root / "tests/python/bl_id_ui_name_libraries.py"),
        ("factory", root / "tests/python/bl_id_ui_name_factory.py"),
        ("sculpt", root / "tests/python/bl_id_ui_name_sculpt.py"),
        ("brush-example", version / "reference/brush_rename_example.py"),
        ("node-example", version / "reference/node_rename_example.py"),
        ("other-names-example", version / "reference/other_names_example.py"),
    )
    started_at_utc = datetime.now(timezone.utc).isoformat()
    checks = [run_check("core", core_command, artifacts, args.timeout, report)]
    for name, script in scripts:
        command = blender_command + ["--python", str(script)]
        checks.append(run_check(name, command, artifacts, args.timeout))
    command = [sys.executable, "-B", "-m", "unittest", "discover",
               "-s", str(version / "reference"), "-p", "test_*.py", "-v"]
    checks.append(run_check("reference", command, artifacts, args.timeout))
    passed = all(check["passed"] for check in checks)
    summary = {"passed": passed, "started_at_utc": started_at_utc,
               "blender": str(args.blender.resolve()), "gtest": str(args.gtest.resolve()),
               "checks": checks}
    (artifacts / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                           encoding="utf-8")
    print(f"Review {'passed' if passed else 'failed'}. Evidence: {artifacts}")
    return 0 if passed else 1


is_main_module = __name__ == "__main__"
if is_main_module:
    sys.exit(main())
