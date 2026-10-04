# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Author display-name notes in approved bundled asset files.

Run Blender with the file and this script, then pass ``-- --write-source``.
Eligibility follows the explicit file manifest and existing asset marks,
never the spelling of a name. Ordinary user files are refused.
"""

import argparse
import json
from pathlib import Path
import sys

import bpy


MANIFEST = Path(__file__).with_name("blend_ui_name_factory_files.json")


def author_file(filepath: Path, write_source: bool) -> dict:
    """Mark existing local assets in one explicitly approved source file."""
    root = Path(__file__).resolve().parents[2]
    approved = {root / name for name in json.loads(MANIFEST.read_text())}
    is_approved = filepath in approved
    if not is_approved:
        raise ValueError("File is outside the reviewed factory asset manifest")
    is_loaded_source = Path(bpy.data.filepath).resolve() == filepath
    if not is_loaded_source:
        raise ValueError("Load the approved source before authoring its names")
    assets = [item for item in bpy.data.user_map() if item.library is None and item.asset_data is not None]
    has_assets = bool(assets)
    if not has_assets:
        raise ValueError("Approved source contains no assets")
    for item in assets:
        item.ui_name_translation_mark()
        assert item.ui_name_is_translatable
    names = sorted((item.bl_rna.identifier, item.name) for item in assets)
    if write_source:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(filepath), compress=True)
    return {"file": str(filepath), "marked": len(names), "names": names, "saved": write_source}


def main() -> None:
    """Parse Blender script arguments and report the explicit authoring result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-source", action="store_true")
    has_script_arguments = "--" in sys.argv
    arguments = sys.argv[sys.argv.index("--") + 1:] if has_script_arguments else []
    args = parser.parse_args(arguments)
    result = author_file(Path(bpy.data.filepath).resolve(), args.write_source)
    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
