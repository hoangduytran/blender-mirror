# Verify the shared name presentation

Updated 2026-10-04. Use the Blender and test executable built from this branch. These scripts use Blender's APIs and Python's standard library; they install no packages. They keep test preferences in fresh folders.

For a 10–15 minute first check and the full step-by-step plan, see [Developer test plan](DEVELOPER_TEST_PLAN.md). Its explanations use everyday English and keep exact commands ready to copy.

For core discussion, [a smaller approach](20261004_125416_core_review_simplification_note.md) maps proposed removals and reductions to the current files. These are alternatives for review, not changes already made.

## Automated checks

From the repository root, with your build paths substituted:

```sh
python3 project_files/issues/20260924_labelling_in_i18n/version_0002/review/run_review_tests.py \
  --blender ../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --gtest ../build_darwin_full/bin/tests/blender_test \
  --release-dir ../build_darwin_full/bin/Blender.app/Contents/Resources/5.3 \
  --output-dir /tmp/blender-name-review
```

Check the runner itself with `python3 project_files/issues/20260924_labelling_in_i18n/version_0002/review/test_review_runner.py`. Its six cases verify success, child failure, an empty C++ filter, missing editing coverage, missing selection-color coverage and a missing named Browser FileList case, including paths with spaces.

The runner produces a fresh `run-*` folder with commands, logs, C++ XML and `summary.json`. A missing, skipped, incomplete or failing C++ report fails the run. There are nine checks: C++ names/assets/operators; Python API; libraries; approved factory files and extraction; actual Sculpt Mode activation; three demonstration scripts; and the 26-test small reference model. The reference model is an explanation, not evidence of Blender UI behavior.

Expected focused C++ minimum: 30 shared-name cases, seven UI editing cases, three registered-tool/external-file cases and 77 total cases. The current script checks minima so a later added test does not break the runner. The actual cold/warm Browser FileList case must be present by name. All selected cases must pass.

Undo needs a real foreground Blender window and is separate:

```sh
../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --factory-startup --python-exit-code 1 \
  --python tests/python/bl_id_ui_name_undo.py -- \
  --report /tmp/name-undo.json
```

Read the JSON `passed` field and its individual checks. Do not treat process exit alone as proof: the script closes Blender after recording either outcome. Use an isolated user configuration folder when running manually.

## Visible checks for ordinary reviewers

Open the rebuilt application, not an older installed Blender. Enable Vietnamese and **Interface Translation** under Preferences → Interface → Translation. Keep **Translate New Data** enabled during this check to ensure language switching does not rename saved tool IDs.

1. **Workspaces:** start a fresh factory session. Switch English → Vietnamese → English. Tabs should follow available translations. Open a name edit: it should contain the current displayed translation, with the caret at the end and no automatic selection. Rename one tab personally and rename it back; it should remain literal. Canceling or confirming unchanged text should preserve permission.
2. **Brushes:** enter Sculpt Mode on the default cube. Select the Essentials **Smooth** brush. With Vietnamese enabled, compare the header, shelf and tooltip to the Brush-context translation. Toggle Interface Translation off/on. Save and reopen the scene, then select the same brush again. Save a personal copy and rename it; its label must stay literal, even after renaming back.
3. **Node tool:** use a marked group configured as a node tool. Check its registered menu/search label in both languages. Rename, undo and redo; the label and search alias must refresh. A node instance's custom title stays as written. A marked ordinary node group uses the same shared name rule.
4. **Assets:** browse Essentials and a temporary external asset library. Search by source name and the displayed translation; each asset should appear once. Toggle translation and switch language while the search remains open. A missing translation shows source. Browsing must not import the asset.
5. **Editing and identity:** rename through a visible field, Outliner and Python; verify literal display and unchanged unrelated items. Create a duplicate and a `.001` collision. Save/reopen. Exercise linked data, append and library overrides using the automated library fixtures and observe the same labels in the UI.

A prepared four-case panel is available with:

```sh
../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --factory-startup --python tests/python/bl_id_ui_name_gui.py -- \
  --output-dir /tmp/name-gui
```

The panel shows a plain **Stored name** line read directly from `ID.name`. The user has clarified that **Edit name** must start with the selected-language presentation as well. The updated build starts editing with that presentation: unchanged confirmation preserves the stored source and eligibility; a real edit saves the user’s text literally and clears eligibility. Both checkouts have the same final source and passing verification. On entry, check that Space appends to the whole translated name and Backspace removes only its last character. For personal names too, Space must append at the end caret. Select All must show a visible highlight and allow a full replacement. Cancel each trial to keep the source name and eligibility unchanged.

The node group has a real, stable tool operator identifier. In F3 search, compare “Review Node Tool Source” with “Nhóm nút mẫu” after switching language; inspect the menu result without executing the empty example tool.

For a real external-file check, add `--with-external-library` after the script’s `--output-dir` argument. Choose **Name Review External** in the Asset Browser. Its one object asset is stored as **Review External Asset Source** and presented as **Tài nguyên ngoài mẫu** in Vietnamese. Search either spelling. This file is written separately and its object removed from the current scene/data before browsing; language reports include `external_asset_imported: false`. Do not drag or append it during the pre-import check. The fixture registers this library only in the isolated running preferences and does not save preferences.

This panel uses test translations to demonstrate the rule even where a factory catalog has no entry. It does not replace the real Sculpt Mode/Essentials/catalog check above. See the script's arguments for optional evidence output.

Record the exact build/commit, locale, Interface Translation setting, action and visible result. Capture workspace, actual Sculpt brush, registered node tool and Asset Browser views. API JSON and a successful launch log are not screenshots and must not be reported as visible verification.

## Broader checks

The configured existing Python regression gate can be run with:

```sh
ctest --test-dir ../build_darwin_full --output-on-failure \
  -R '^(id_management|blendfile_library_overrides|script_pyapi_idprop|script_pyapi_idprop_datablock|bl_node_copy_operators|bl_node_group_compat|bl_node_group_interface)$'
```

Use the existing ID-property/remapping/brush/asset/string-search C++ suites and Python ID management, library-override, ID-property and node-group compatibility/interface tests. Exact executed selections and results belong in [verification](../20261003_231111_verification.md). Report skipped or unavailable gates explicitly.

## Authoring bundled names

Factory permission is saved in reviewed asset sources. `tools/utils/blend_author_ui_names.py` only accepts the explicit factory manifest and requires `--write-source` to save. Review ordinary brush settings, node topology, catalogs and previews against the original sources when updating these files. Never run this authoring operation on users' libraries as part of startup or import.

## Reproduce the factory preservation comparison

Use the original source files from the parent of the feature commit in a separate directory, with real Git LFS content. Keep their original `assets/` layout and linked dependencies. Then run:

```sh
../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --python-exit-code 1 \
  --python project_files/issues/20260924_labelling_in_i18n/version_0002/review/compare_factory_files.py -- \
  --baseline-dir /path/to/original-source-tree \
  --output-dir /tmp/name-factory-comparison
```

The script reads both sides without saving, checks their hashes remain unchanged, records each differing field and fails on differences. The report names excluded runtime/API fields and the intended author note. It compares RNA-visible Brush/NodeTree settings and owned nested data; other ID references are compared by type, name and library basename. It does not claim to compare every DNA field or every referenced ID's internal contents.

### Reproduce the first-keystroke check

The earlier workspace branch already supplied this test approach. Blender’s existing event-test setup runs inside a temporary application, opens the real name editor, types Space before selecting any text, and reads back the actual buffer. It checks that the entire translated name remains, followed by Space.

```bash
BLENDER_USER_RESOURCES="/tmp/name-ui-resources" \
"/path/to/Blender.app/Contents/MacOS/Blender" \
  --factory-startup --gpu-backend metal --no-native-pixels \
  --no-window-frame -p 0 0 800 600 --enable-event-simulate \
  --python tests/python/ui_simulate/run_blender_setup.py -- \
  --tests test_workspace.ui_name_editing_space_appends
```

This check passed in the rebuilt original application. It exercises the real RNA name field and workspace tab, seven name/language states in both controls (14 variants), a long supplied translation, Vietnamese text input, Escape and unchanged Enter. A separate C++ test checks that the actual drawing color contrasts with both default tab backgrounds; manually verify the visible highlight too. Consult the verification document for the current independent and destination results.

The command above is the tested macOS window setup; use a fresh resources folder so review preferences remain separate. The test asks Blender to redraw the header through its normal event loop before finding each editor. Use the direct Blender command above for this check: its exit code belongs to the application running the assertions. The outer `run.py` helper can return zero even when it reports a failed child; that value is not accepted as proof here.

### Actual external Browser list

The focused C++ gate includes `RegisteredNodeToolDisplayNameTest.ExternalFileListColdAndWarmTranslatedSearch`. It saves a marked brush in a separate file, frees the authored data, reads it through the Browser’s real FileList, and checks an actual cold index miss followed by a warm hit. Both source and translated queries must return the same single entry. The test also checks disabled/English fallback, unchanged-query refiltering, unchanged source bytes/references and no imported IDs. It explicitly requests refiltering; it does not assert notifier delivery or pixels.
