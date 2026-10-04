# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check that the reviewer runner detects failure and accepts paths containing spaces."""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RUNNER = pathlib.Path(__file__).with_name("run_review_tests.py")

class ReviewRunnerTest(unittest.TestCase):
    def run_case(self, core_fails=False, empty_filter=False, missing_edit_suite=False, missing_tab_selection_case=False, missing_external_filelist_case=False):
        with tempfile.TemporaryDirectory(prefix='review runner fixture ') as directory:
            root = pathlib.Path(directory)
            stub = root / 'stub executable.py'
            trace = root / 'trace.jsonl'
            stub.write_text('#!/usr/bin/env python3\n'
                'import json,pathlib,sys\n'
                f'trace=pathlib.Path({str(trace)!r})\n'
                'with trace.open("a") as output: output.write(json.dumps(sys.argv)+"\\n")\n'
                'xml_argument=next((value for value in sys.argv if value.startswith("--gtest_output=xml:")),None)\n'
                'has_xml_argument = xml_argument is not None\n'
                'if has_xml_argument:\n'
                ' path=pathlib.Path(xml_argument.split("xml:",1)[1]);path.parent.mkdir(parents=True,exist_ok=True)\n'
                f' count={0 if empty_filter else 77}\n'
                ' suites="<testsuites tests=\\\"%d\\\" failures=\\\"0\\\" errors=\\\"0\\\" disabled=\\\"0\\\">" % count\n'
                f' for name,total in (("IDUINameTest",30),("IDNameEditTest",{0 if missing_edit_suite else (6 if missing_tab_selection_case else 7)}),("RegisteredNodeToolDisplayNameTest",3),("ExistingTest",{44 if missing_edit_suite else (38 if missing_tab_selection_case else 37)})):\n'
                '  actual=total if count else 0\n'
                '  suites+="<testsuite name=\\\"%s\\\" tests=\\\"%d\\\" failures=\\\"0\\\" errors=\\\"0\\\" disabled=\\\"0\\\">"%(name,actual)\n'
                f'  has_filelist_case=name=="RegisteredNodeToolDisplayNameTest" and not {missing_external_filelist_case!r}\n'
                '  suites+="".join("<testcase name=\\\"Case%d\\\" classname=\\\"%s\\\"/>"%(number,name) for number in range(actual))+"</testsuite>"\n'
                '  if has_filelist_case: suites=suites.replace("Case0\\\" classname=\\\"RegisteredNodeToolDisplayNameTest","ExternalFileListColdAndWarmTranslatedSearch\\\" classname=\\\"RegisteredNodeToolDisplayNameTest")\n'
                ' path.write_text(suites+"</testsuites>")\n'
                f' sys.exit({1 if core_fails else 0})\n'
                'print("successful stub execution")\n')
            stub.chmod(0o755)
            result = subprocess.run([sys.executable, str(RUNNER), '--blender', str(stub), '--gtest', str(stub), '--output-dir', str(root / 'output with spaces')], capture_output=True, text=True)
            summaries=list((root / 'output with spaces').glob('run-*/summary.json'))
            self.assertEqual(len(summaries),1,msg=result.stderr)
            summary=json.loads(summaries[0].read_text())
            self.assertEqual(len(summary['checks']),9)
            self.assertEqual({check['name'] for check in summary['checks']},{'core','python-api','libraries','factory','sculpt','brush-example','node-example','other-names-example','reference'})
            for check in summary['checks']:
                log=pathlib.Path(check['log'])
                self.assertTrue(log.is_file(),msg=str(log))
            self.assertEqual(len(trace.read_text().splitlines()),8)
            return result.returncode,summary

    def test_all_success_and_space_paths(self):
        code,summary=self.run_case()
        self.assertEqual(code,0)
        self.assertTrue(summary['passed'])
        self.assertTrue(all(check['passed'] for check in summary['checks']))

    def test_child_failure_keeps_running(self):
        code,summary=self.run_case(core_fails=True)
        self.assertNotEqual(code,0)
        self.assertFalse(summary['passed'])
        self.assertFalse(next(check for check in summary['checks'] if check['name']=='core')['passed'])
        self.assertTrue(all(check['passed'] for check in summary['checks'] if check['name']!='core'))

    def test_empty_gtest_filter_is_failure(self):
        code,summary=self.run_case(empty_filter=True)
        self.assertNotEqual(code,0)
        self.assertFalse(summary['passed'])

    def test_missing_edit_suite_is_failure(self):
        code,summary=self.run_case(missing_edit_suite=True)
        self.assertNotEqual(code,0)
        self.assertFalse(summary['passed'])

    def test_missing_tab_selection_case_is_failure(self):
        code,summary=self.run_case(missing_tab_selection_case=True)
        self.assertNotEqual(code,0)
        self.assertFalse(summary['passed'])

    def test_missing_external_filelist_case_is_failure(self):
        code,summary=self.run_case(missing_external_filelist_case=True)
        self.assertNotEqual(code,0)
        self.assertFalse(summary['passed'])

is_main_module = __name__ == "__main__"
if is_main_module:
    unittest.main()
