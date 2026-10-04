# Developer test plan: translated display names

Updated 2026-10-04. This plan tests the completed local implementation. The design remains a proposal for Blender review by Blender developers, not upstream approval. No extra software package is needed.

## Quick reviewer check: 10–15 minutes

Use the newly built Blender and fresh settings from section 2. Do not use an older installed application.

1. Launch `"$B" --factory-startup`. In Preferences → Interface → Translation choose English, then Vietnamese, with Interface Translation on. Keep Translate New Data on. Layout should display **Bố Trí** in Vietnamese. In Python Console inspect `bpy.context.workspace.name` and `bpy.context.workspace.ui_name_is_translatable`: the source is still `Layout`, permission to translate is true. See section 5.
2. Select the cube, enter Sculpt Mode and activate the Essentials **Smooth** brush. The header and shelf tooltip should show **Làm Mịn** in Vietnamese; the stored brush name remains `Smooth`. Turn Interface Translation off/on and compare. See section 6.
3. Search the brush shelf by `Smooth`, then by pasted `Làm Mịn`: the same brush is found. Keeping the Vietnamese search text should stop finding that translation when translation is disabled and match again when enabled.
4. Double-click the workspace tab. Text must start in the chosen display language, with the cursor at the end and no text selected. Space adds a space at the end; Esc cancels without changing the source. Repeat, use Select All and check visible highlighting. Rename to `Review Personal Workspace` and confirm it stays exactly as written in both languages. Rename back to `Layout`; it must stay as Layout and without permission to translate.
5. Save a disposable file, reopen it, and confirm the personal workspace's stored name, removed translation permission and unchanged displayed name survive reopening. Reactivate Smooth and confirm the unchanged factory brush still translates.

Record which Blender you used, its settings and what you saw. This quick check shows the main idea; the full plan below covers the remaining checks.

## 1. Purpose and scope

Check one shared name rule for workspaces, brushes, node groups used as tools, and assets. The rule works beyond workspaces. Translation changes what people see, never the saved name (`ID.name`). Personal names and names without permission stay as written. Where name search is supported, both the saved and translated name find the same item. The rule must survive saving, reopening and using items from other files.

Individual node titles, socket names, asset tags, descriptions and asset folder names keep their existing rules. Other saved items can also be marked for translation. An item does not gain permission merely because of its type or familiar spelling. [Design](../20261003_231111_generic-name-localization-design.md), [exact implementation](../20261003_231111_implementation-analysis.md), [final verification](../20261003_231111_verification.md).

Using an item from another file leaves that item owned by the original file (Blender calls this **Link**). Bringing a local copy into your file is **Append**. Making an editable local version while keeping its connection to the original is **Library Override**. The steps below use these exact Blender menu names.

## 2. Before you start: build and identify Blender

Run shell commands from the repository root. Completed records before this plan:

| Checkout | Branch | Verified review record |
| --- | --- | --- |
| Original | `feature/generic-ui-name-translation` | `27a622d19bd81d923e3fcc627864b61001475211` |
| Second | `feature/generic-ui-name-review` | `fc88598d8fd783287c09fa0c82ece6ccda1193e7` |

This plan and its document-only commit do not change the tested Blender code. The last production correction is `9d6c903c247` / `d8735998d4e`; final external Browser test coverage is `d72f0ad5721` / `b15865455c8`. Older evidence hashes are explained by the [identity maps](../20261004_121634_commit_identity_verification.md).

The completed checks used an Apple Silicon Mac and a Release build, with translation and the program checks enabled. Both Ninja and Unix Makefiles builds passed. Typing, undo and visible checks need a Blender window. Run them one at a time and keep that window active. Other systems can run the file checks with their own Blender paths. Their keyboard setup has not been checked here.

Have Blender's usual compiler, CMake and platform libraries already installed. Factory assets and `tests/files` must contain real Git LFS content, not pointer files. Install the built resources/translation lists and Essentials assets. No account or network asset library is needed.

```sh
BUILD_DIR=../build_darwin_full
P=project_files/issues/20260924_labelling_in_i18n/version_0002
E=$(mktemp -d /tmp/blender-ui-name-review.XXXXXX)
B="$BUILD_DIR/bin/Blender.app/Contents/MacOS/Blender"
T="$BUILD_DIR/bin/tests/blender_test"
L="$BUILD_DIR/bin/tests/BLI_test"
R="$BUILD_DIR/bin/Blender.app/Contents/Resources/5.3"
mkdir -p "$E/config" "$E/datafiles" "$E/scripts" "$E/extensions"
export BLENDER_USER_CONFIG="$E/config"
export BLENDER_USER_DATAFILES="$E/datafiles"
export BLENDER_USER_SCRIPTS="$E/scripts"
export BLENDER_USER_EXTENSIONS="$E/extensions"
git branch --show-current
git rev-parse HEAD
```

For the second checkout substitute `BUILD_DIR=../build_darwin` before assigning executable paths. The variables are shell-local review paths, not changes to your normal preferences.

For a new build, use the existing release settings below. For an existing build, check its saved settings before rebuilding:

```sh
cmake -S . -B "$BUILD_DIR" -C build_files/cmake/config/blender_release.cmake \
  -DCMAKE_BUILD_TYPE=Release -DWITH_INTERNATIONAL=ON -DWITH_GTESTS=ON \
  -DWITH_TESTS_SINGLE_BINARY=ON -DWITH_TESTS_BATCHED=ON
cmake --build "$BUILD_DIR" --target install blender_test BLI_test --parallel 4
rg '^(CMAKE_BUILD_TYPE|WITH_INTERNATIONAL|WITH_GTESTS|WITH_TESTS_SINGLE_BINARY|WITH_TESTS_BATCHED):' \
  "$BUILD_DIR/CMakeCache.txt"
"$B" --version
"$B" --background --factory-startup --python-exit-code 1 --python-expr \
  "import bpy; print(bpy.app.binary_path, bpy.app.version_string, bpy.app.build_hash); assert bpy.types.ID.bl_rna.properties.get('ui_name'); assert bpy.types.ID.bl_rna.functions.get('ui_name_translation_mark'); assert 'vi_VN' in bpy.context.preferences.view.bl_rna.properties['language'].enum_items"
```

Expected: Release; all four switches ON; the exact requested Blender path; the new Python commands and Vietnamese are available. Missing assets/translation lists are setup failures, not passing fallback coverage. The version text can show an older commit after a partial rebuild or a document-only commit. Record both the version text and the current Git commit, together with the build log. Start the exact executable with `"$B" --factory-startup`; on macOS `open -n` alone does not prove which binary another already-open window uses. In that window's Console confirm `bpy.app.binary_path` again.

Select Vietnamese using Preferences or the actual Python commands:

```python
view = bpy.context.preferences.view
view.language = 'vi_VN'
view.use_translate_interface = True
view.use_translate_new_dataname = True
```

## 3. How the displayed name is chosen

```text
saved name + permission to translate + chosen language and available translation = displayed name
```

There are three possible results: the saved default name (`USE_DEFAULT`), an available translation (`USE_TRANSLATION`), or a personal name (`USE_USERDEFINE`). Only one name is saved. A marked item shows its translation when Interface Translation is on and a translation exists. Otherwise it shows its saved name. A real rename removes permission and shows the new text exactly as written. Old or unmarked names stay unchanged. Switching language never rewrites `ID.name`.

## 4. Automated commands and expected results

Commands use the section 2 variables. Retain exit codes, XML, JSON and logs from new runs. The counts below are checked against the current tests and recorded final reports, not inferred from a successful launch.

### 4.1 Run the nine reviewer checks and check their runner

Purpose: run the 77 main program checks, Python commands, libraries, factory/extraction, actual Sculpt activation, three examples and explanatory reference model.

```sh
python3 "$P/review/run_review_tests.py" --blender "$B" --gtest "$T" \
  --release-dir "$R" --output-dir "$E/review"
python3 -B "$P/review/test_review_runner.py"
```

Expected: runner exit 0, `run-*/summary.json` has `passed: true` and nine passing checks; six runner self-checks pass. Breakdown: 77 main program checks; Python commands 10; libraries 4; factory/extraction 3; Sculpt 1; three example scripts; reference 26. Counts are fixed for this record; the runner accepts at least these counts to allow future additions and requires the named real Browser-list check. No skipped program checks are accepted.

Files: [runner](run_review_tests.py), [self-checks](test_review_runner.py), [Python commands](../../../../../tests/python/bl_id_ui_name.py), [libraries](../../../../../tests/python/bl_id_ui_name_libraries.py), [factory](../../../../../tests/python/bl_id_ui_name_factory.py), [Sculpt](../../../../../tests/python/bl_id_ui_name_sculpt.py), [reference](../reference/README.md). [Original summary](evidence/20261004-original/external-browser-final-summary.json), [second summary](evidence/20261004-destination/external-browser-final-summary.json).

### 4.2 Run the 77 main program checks and the separate Browser check

Purpose: the shared name rule, search, items from other files, name editing, highlight colors, tool labels, and the first and second reads of an external asset list.

```sh
"$T" --gtest_filter='IDUINameTest.*:LibID*.*:AssetMetadataTest.*:AssetRepresentationTest.*:OperatorDisplayNameTest.*:RegisteredNodeToolDisplayNameTest.*:IDNameEditTest.*' \
  --gtest_output="xml:$E/core.xml" --test-assets-dir="$PWD/tests/files" --test-release-dir="$R"
"$T" --gtest_filter=RegisteredNodeToolDisplayNameTest.ExternalFileListColdAndWarmTranslatedSearch \
  --gtest_output="xml:$E/filelist.xml" --test-assets-dir="$PWD/tests/files" --test-release-dir="$R"
```

Expected: 77/77 (30 shared-name, seven editing/color, three registered/external, 37 selected existing cases); standalone 1/1. No failures, errors, disabled tests or skipped tests. The first read must read the asset file; the second must use the saved search index. Both saved-name and translated-name searches return the same item without importing it or changing its file. Blender needs a writable folder for the saved search index. The test explicitly requests filtering again; it does not prove automatic refresh messages or what appears on screen.

Files: [shared-rule tests](../../../../../source/blender/blenkernel/intern/id_ui_name_test.cc), [editing tests](../../../../../source/blender/editors/interface/interface_ops_test.cc), [tool-label and Browser-list tests](../../../../../source/blender/windowmanager/intern/wm_operator_type_test.cc). [Final XML](evidence/20261004-original/external-browser-final-core.xml).

### 4.3 Run the 40 related program checks: 37 + 3

Purpose: existing ID properties/remapping, brushes, asset libraries, driver copying and approximate string search.

```sh
"$T" --gtest_filter='IDPropertyTest.*:LibRemapTest.*:BrushTest.*:AssetLibraryTest.*:AssetLibraryServiceTest.*:CopyDriversToSelected.*' \
  --gtest_output="xml:$E/nearby.xml" --test-assets-dir="$PWD/tests/files" --test-release-dir="$R"
"$L" --gtest_filter='string_search.*' --gtest_output="xml:$E/string-search.xml"
```

Expected: 37/37 and 3/3. String search is in **BLI_test**, not blender_test. Relevant files: `source/blender/blenkernel/intern/{idprop,lib_remap,brush}_test.cc`, asset-system tests under `source/blender/asset_system/tests/`, `source/blender/blenlib/tests/BLI_string_search_test.cc`, and `source/blender/editors/interface/interface_ops_test.cc` for driver copying. Use retained `selection-final-*` XML in the [evidence index](evidence/README.md) to compare the exact case list.

### 4.4 Run the seven existing Python test groups

Purpose: check ID management/properties, existing overrides and node copy/compatibility/interfaces. On a set-up build:

```sh
ctest --test-dir "$BUILD_DIR" -N \
  -R '^(id_management|blendfile_library_overrides|script_pyapi_idprop|script_pyapi_idprop_datablock|bl_node_copy_operators|bl_node_group_compat|bl_node_group_interface)$'
ctest --test-dir "$BUILD_DIR" --output-on-failure \
  -R '^(id_management|blendfile_library_overrides|script_pyapi_idprop|script_pyapi_idprop_datablock|bl_node_copy_operators|bl_node_group_compat|bl_node_group_interface)$'
```

Expected: all seven selected entries exist and pass. Zero selected tests is a setup failure. The same scripts can be run directly with the verified flags and data paths:

```sh
for script in bl_id_management.py bl_pyapi_idprop.py bl_pyapi_idprop_datablock.py; do
  "$B" --background --console-crash-handler --factory-startup --debug-memory \
    --debug-exit-on-error --python-exit-code 1 \
    --python-expr "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'" \
    --python "tests/python/$script" || break
done
"$B" --background --console-crash-handler --factory-startup --debug-memory \
  --debug-exit-on-error --python-exit-code 1 \
  --python-expr "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'" \
  --python tests/python/bl_blendfile_library_overrides.py -- \
  --output-dir "$E/override-files" --test-dir "$PWD/tests/files/libraries_and_linking"
for script in bl_node_copy_operators.py bl_node_group_compat.py bl_node_group_interface.py; do
  "$B" --background --console-crash-handler --factory-startup --debug-memory \
    --debug-exit-on-error --python-exit-code 1 \
    --python-expr "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'" \
    --python "tests/python/$script" -- --testdir "$PWD/tests/files/node_group" || break
done
```

Inspect each command's result; stopping a loop after a failure is not a complete run. Expected test counts: ID management 8, ID properties 39, node copy 5, compatibility 6, interface 25. The library-override and ID-property-datablock helper scripts use their own checks; do not invent test counts for them. All seven scripts are in `tests/python/` with the names above. Give each suite fresh writable preference directories when repeating isolated runs. A restricted thumbnail-write abort occurred earlier in the saved item helper and passed unchanged on rerun; preserve both outcomes rather than removing debug flags or calling the failed run a success.

### 4.5 Type in the actual name fields: 14 cases

Purpose: type into the normal name field and the workspace tab in seven situations each. Check Space, Đ, Esc, and pressing Enter without changing the name.

```sh
BLENDER_USER_RESOURCES="$E/typing-resources" "$B" \
  --factory-startup --gpu-backend metal --no-native-pixels --no-window-frame \
  -p 0 0 800 600 --enable-event-simulate \
  --python tests/python/ui_simulate/run_blender_setup.py -- \
  --tests test_workspace.ui_name_editing_space_appends
```

Expected: direct application exit 0 and no check failure; 7 × 2 = 14 variants. States include personal, unmarked, translation OFF, English, missing entry, actual Vietnamese and a long translated name. Files: [test](../../../../../tests/python/ui_simulate/test_workspace.py), [setup](../../../../../tests/python/ui_simulate/run_blender_setup.py). Use this direct command; the outer event runner can report exit 0 despite a failed child. Keep its window focused. Selection contrast also has a C++ check; actual highlight visibility remains a manual check.

### 4.6 Undo and redo in a Blender window: three cases

```sh
BLENDER_USER_RESOURCES="$E/undo-resources" "$B" --factory-startup --python-exit-code 1 \
  --python tests/python/bl_id_ui_name_undo.py -- --report "$E/undo.json"
cat "$E/undo.json"
```

Purpose: real rename, duplicate and forced-same-name clash undo/redo. Expected JSON `passed: true` and all three named checks; no Python error. The script quits after either outcome, so process exit alone is insufficient. [Source](../../../../../tests/python/bl_id_ui_name_undo.py). Undo checkpoints for changing translation permission can also be reviewed manually in section 18.

### 4.7 Check the supplied files and their translation marks

See section 21 for unchanged original copy preparation and the exact comparison/authoring commands. Expected: 15 files / 353 brushes and node groups, no recorded differences beyond the intended note and documented exclusions; neither input changes. The nine-check test group already verifies saved marks/extraction and refusal of unapproved authoring.

## 5. Workspace manual test

1. In a fresh factory file record Layout in English. Change to Vietnamese: tab becomes Bố Trí. Use Console:

```python
ws = bpy.context.workspace
source = ws.name
print(ws.name, ws.ui_name, ws.ui_name_is_translatable, ws.ui_name_translation_context)
assert source == 'Layout' and ws.ui_name_is_translatable
```

2. Switch Interface Translation OFF, then ON. `ws.name == source` throughout; display toggles source/translation. English returns source. Other factory tabs follow available entries.
3. Double-click the tab in Vietnamese. It begins with the displayed text, not English source, and the cursor at the end with no text selected. Space must add a space at the end, Backspace removes one character, and Select All shows a visible selection. Esc or unchanged Enter retains source/permission to translate.
4. Rename through the tab to `Review Personal Workspace`. In Console find again the item; translation permission off and `ui_name == name` are expected. Switch both languages; rename back to `Layout` and confirm it stays as Layout and without permission to translate.
5. Before save/reload, use Edit → Undo/Redo (or macOS Cmd+Z / Shift+Cmd+Z) to inspect the rename restoration. Do not assume Console assignments create their own undo steps.
6. Save a disposable `.blend`; reopen and inspect again. find again IDs after reopening; old Python references are invalid. Do not restore permission to translate merely to make a rename-back test pass.

Proof: [typing test](../../../../../tests/python/ui_simulate/test_workspace.py), [final visible results](../20261003_231111_verification.md#actual-visible-checks).

## 6. Real Sculpt brush: Essentials, not the demonstration brush

1. Fresh factory session, cube selected. Enter Sculpt Mode. Select Essentials Smooth in the asset shelf or header brush selector. Compare the shelf tooltip, header and popover in English and Vietnamese. Expected Smooth / Làm Mịn. If the shelf hides labels, hover for the name.
2. Confirm source/permission to translate in Console; mode state remains Sculpt even if another editor is temporarily a Console:

```python
brush = bpy.context.tool_settings.sculpt.brush
print(brush.name, brush.ui_name, brush.ui_name_is_translatable, brush.library)
assert brush.name == 'Smooth' and brush.ui_name_is_translatable
```

To activate the precise tested asset through the supported Blender command (with a Sculpt session active):

```python
bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth')
```

3. Search the shelf/popover by Smooth and Làm Mịn. Confirm one matching asset identity; retain a translated search text while toggling translation. Repeat OFF/ON and English. Never require translation when the translation list lacks an entry.
4. Save/reopen; reactivate the same Essentials brush. `brush.name` must still be Smooth. Do not edit or save the shipped library to test a personal rename.
5. Create the tested local personal copy via Brush Save As, using the current-file/local library. The exact Python commands used by the Sculpt integration test is:

```python
bpy.ops.brush.asset_save_as(name='Review Personal Smooth', asset_library_reference='LOCAL', catalog_path='')
brush = bpy.context.tool_settings.sculpt.brush
assert brush.name == 'Review Personal Smooth'
assert not brush.ui_name_is_translatable and brush.ui_name == brush.name
```

6. Rename the local copy through its editable name field; switch languages and save/reopen. It remains exactly as written. Rename it to Smooth: translation permission stays off, even if Blender adds a number to avoid using the same name twice. For deterministic .001/.002 cases use section 17. A plain `brush.copy()` is also a user copy and is exactly as written; it need not become the active brush automatically.

Proof: [Sculpt test](../../../../../tests/python/bl_id_ui_name_sculpt.py), [brush example](../20261004_001238_brush-renaming-example.md), [user-recorded results](../20261003_231111_verification.md#actual-visible-checks). The review panel's Cọ mẫu brush is not an Essentials/Sculpt substitute.

## 7. Actual registered node-tool path

Launch the supplied example setup, which adds a real GeometryNodeTree tool for Object Mode on a mesh:

```sh
"$B" --factory-startup --python tests/python/bl_id_ui_name_gui.py -- \
  --output-dir "$E/gui" --with-external-library
```

Press N in the 3D View and open **Name Review**. The panel's English/Vietnamese buttons switch language and Interface Translation. All four selectors are real standard item selectors; Stored name is an plain line showing the saved name.

1. Stay in Object Mode with the cube selected. F3 search `Review Node Tool Source`, then paste `Nhóm nút mẫu`. Inspect the result without executing the empty example tool. Both should locate the same registered tool in Vietnamese; English uses the source label and removes its Vietnamese alternative search name.
2. Inspect `g = bpy.context.scene.review_node_group`; `g.name` is the source, `g.ui_name_is_translatable` true, `g.node_tool_idname` is `geometry.review_ui_name_gui`. The stable tool command name is not translated.
3. Rename through the panel's Edit name field to My Tool, confirm exactly as written F3 result/search, Undo/Redo and rename-back. Observe the refreshed tool label without reauthoring. Use the panel's Save and Reopen Review Copy for same running Blender saving and reopening.
4. An ordinary marked node group uses the same ID presentation rule. Individual `node.name`, `node.label` and socket names are separate authored fields; they are not a claim of this tool integration.

The function that chooses the tool label reads its saved permission note and the current language. It does not bring the asset into the file just to show a label. The internal `name_requires_properties` setting lets this tool show its name without extra tool settings; other tools keep their existing behavior. Reviewers do not need to set it. This check covers the actual example tool, not every possible node menu. [Registered tests](../../../../../source/blender/windowmanager/intern/wm_operator_type_test.cc), [registration source](../../../../../source/blender/editors/geometry/node_group_operator.cc), [example setup](../../../../../tests/python/bl_id_ui_name_gui.py).

The example translations live only in this running Blender. Saving an item does not save the translations. Reopening a file in the same Blender keeps them available. After restarting Blender, add the same translation list again before expecting the example translations. Without it, showing the saved name is correct. Running the whole setup script again creates and marks new examples; that is not a check of saved personal names.

## 8. Asset Browser and external library

Use the section 7 example setup in a fresh session. Change the bottom editor to Asset Browser and enlarge it.

1. Select Current File; clear search. The marked object asset displays Review Asset Source in English and Tài nguyên mẫu in Vietnamese. Hover and compare tooltip name. The separate personal node tool remains exactly as written after a rename.
2. In Vietnamese search Review, then clear and paste Tài nguyên. Each finds the same single object asset. Hold the Vietnamese search text while selecting English: its translated match disappears; select Vietnamese and it returns.
3. Select **Name Review External**. Before import, one object asset is Review External Asset Source / Tài nguyên ngoài mẫu. Compare tooltip and search Review / Tài nguyên ngoài. Verify no import:

```python
assert 'Review External Asset Source' not in bpy.data.objects
```

4. The example setup writes `gui/external/review-external.blend` once, then removes that object from local data. Record its file digest before and after browsing/language changes; it must not change. No preferences are saved by the example setup.
5. Append via section 15's exact `bpy.data.libraries.load(..., link=False)` procedure, or use File → Append → that file → Object → Review External Asset Source. Expect a local copy, the saved source name and retained translation permission unless a name same-name clash occurred. Rename the imported item, save/reopen, and confirm exactly as written presentation. Browsing alone must not append.
6. Brush asset shelf/header behavior is section 6; the example setup's object asset does not belong in a Sculpt brush picker. An empty brush picker for an object search text is not failed object-asset search.

Proof: [example setup](../../../../../tests/python/bl_id_ui_name_gui.py), [final external manual record](evidence/20261004-original/external-browser-manual.md), [real Browser-list check](../../../../../source/blender/windowmanager/intern/wm_operator_type_test.cc). The source asset `.blend` is never rewritten by browsing or changing language.

## 9. Which names should search find?

The entries below apply to supported item lists, Asset Browser and shelf searches, and F3 search for the example node tool. They do not add search to controls which have none. “Translation” means the available label of that same item, not tags or unrelated approximate matches.

| Item state | Stored/source search text | Translated search text | User-defined search text |
| --- | --- | --- | --- |
| Marked, ON, entry exists | Yes | Yes; same result once | Only if it matches actual text |
| Marked, ON, entry missing | Yes | No translated alternative search name | Only if it matches actual text |
| Marked, OFF or English saved-name display | Yes | No translated alternative search name | Only if it matches actual text |
| User renamed/without permission | Current stored name only | No former alternative search name | Yes |
| Old/unmarked | Current stored name only | No added translated search name | Yes if that is the stored name |

Reproduce with the example setup's object asset or F3 tool: unchanged original copy both queries; OFF; English; ON; personal rename; rename-back. For missing-entry coverage, create a local object asset named `Review Missing Catalog Entry 98765`, mark it, and verify `bpy.app.translations.pgettext_iface(item.name, item.ui_name_translation_context) == item.name` before judging fallback. Search that exact source in Current File. Use a distinctive full search text to avoid legitimate approximate/tag matches. Clear filters and confirm the library/item type before diagnosing missing results.

For the missing-translation case, paste this into the rebuilt Blender's Console:

```python
missing = bpy.data.objects.new('Review Missing Catalog Entry 98765', None)
missing.use_fake_user = True
missing.asset_mark()
missing.ui_name_translation_mark()
assert bpy.app.translations.pgettext_iface(missing.name, missing.ui_name_translation_context) == missing.name
assert missing.ui_name_is_translatable and missing.ui_name == missing.name
```

Find it in Current File in the Asset Browser. Its name stays unchanged because there is no matching translation, even though it has permission.

## 10. What happens when a name changes

| Operation | Stored name | permission to translate | Presentation | Save/reload |
| --- | --- | --- | --- | --- |
| marked for translation original | Source | True | Current entry or source | Preserved |
| language switch | Unchanged | Unchanged | Derived again | Names not rewritten |
| Same saved name assigned by Python commands | Unchanged | Retained | Derived | Preserved |
| Unchanged UI confirmation/Esc | Original source | Retained | Derived | Preserved |
| Real UI/Python commands rename | Final user name | False | exactly as written | Preserved |
| Rename back | Source-looking spelling | False | exactly as written | Preserved |
| User copy/duplicate | Unique final name | False | exactly as written | Preserved if retained |
| Append same-name clash | Numbered final name | False | exactly as written | Preserved |
| Undo/Redo | Restored operation state | Restored with it | Recomputed | Save current state |

Changing a translated editor's text to the English source is still a real UI edit and clears permission to translate, even though it matches the old saved name. This differs from assigning exactly the unchanged saved `.name` through Python. Forced `ID.rename(..., mode='ALWAYS')` can rename the other colliding ID too; every actually changed name loses its permission. [Python commands tests](../../../../../tests/python/bl_id_ui_name.py), [undo source](../../../../../tests/python/bl_id_ui_name_undo.py).

## 11. Save and reopen checks

For each representative, print `(name, ui_name_is_translatable, ui_name)` before save; save a disposable file; reopen; find again the ID and print again in the same language/translation list setup.

| Case | Expected after reopening |
| --- | --- |
| Factory workspace not edited | Original source, true, available translation |
| Factory Smooth | Original source, true, available translation after activating the same asset |
| Fixture node tool | Source, true, test translation in the same translation list-bearing process |
| Fixture asset | Source, true, test translation in the same process |
| Renamed local item | User name, false, exactly as written |
| Collision-adjusted duplicate | Numbered name, false, exactly as written |

Keep unused items in the file by enabling Fake User or adding them to the scene. After reopening, find each item again rather than using an old Python reference. Use UI File → Save As/Open or `bpy.ops.wm.save_as_mainfile(filepath=...)` / `bpy.ops.wm.open_mainfile(filepath=..., load_ui=False)`. The latter preserves current screen layout, not old object handles. [Library tests](../../../../../tests/python/bl_id_ui_name_libraries.py), [examples](../reference/README.md).

## 12. Switch language while Blender is open

With an untouched saved file, record each representative's name, permission to translate, and `bpy.data.is_dirty`. Change only `view.language` English → Vietnamese → English and `view.use_translate_interface` ON/OFF. Return to the same views and unchanged search text; record display and names after each step. No restart is required in the supported paths.

Saved names and translation permission must stay unchanged. Start with a saved file and check that changing only the language does not make Blender show unsaved file changes. A file that already has unsaved changes will still show them. Do not rename, create or mark items during this check. Record any unexpected unsaved-change warning separately: the existing tests prove that names stay unchanged, not how every editor handles that warning.

For missing-entry fallback use section 9's distinctive marked item. Absence of a translation is expected source presentation, not loss of permission to translate. Python commands/typing tests include this case.

## 13. Unmarked items and files made by an older Blender

In Blender without this change (the recorded compatibility check used 4.5.9), create an object named Layout, a Sculpt brush named Smooth, and a GeometryNodeTree named Review Node Tool Source using ordinary `bpy.data.*.new` APIs. Give unused IDs Fake User (keep an otherwise unused item when saving) and save `legacy.blend`. Do not call feature methods in that older Blender.

Paste this setup into the older Blender's Python Console, then note the printed file path:

```python
from pathlib import Path
from tempfile import mkdtemp
legacy_path = Path(mkdtemp(prefix='name-old-file-')) / 'legacy.blend'
old_object = bpy.data.objects.new('Layout', None)
old_brush = bpy.data.brushes.new('Smooth', mode='SCULPT')
old_group = bpy.data.node_groups.new('Review Node Tool Source', 'GeometryNodeTree')
old_object.use_fake_user = old_brush.use_fake_user = old_group.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=str(legacy_path))
print(legacy_path)
```

Open the file with the rebuilt executable, select Vietnamese/Interface Translation, inspect those IDs. All remain unmarked and shown exactly as written even where spelling matches a known factory label. Save a copy, reopen and repeat. Do not use Read Factory Settings between loading and inspecting; that intentionally creates trusted factory workspaces.

If an older Blender is unavailable, create the same unmarked IDs in the new binary and save/reopen; this verifies unmarked behavior but is **not** a check of a file made by an older Blender. The historical actual 4.5.9-produced-file check inspected 14 names. [Python commands negative tests](../../../../../tests/python/bl_id_ui_name.py), [final compatibility result](../20261003_231111_verification.md).

## 14. Use an item from another file

Use a disposable directory with `library.blend` and `consumer.blend`. In a fresh rebuilt Blender's Console, author a local object and write only it to the library:

```python
from pathlib import Path
from tempfile import mkdtemp
directory = Path(mkdtemp(prefix='name-library-review-'))
library = directory / 'library.blend'
item = bpy.data.objects.new('Review Linked Source', None)
item.ui_name_translation_mark()
item.asset_mark()
bpy.data.libraries.write(str(library), {item}, fake_user=True)
bpy.data.objects.remove(item)
```

Register a small review translation list in the Blender that opens the other file; it is not part of the asset file:

```python
bpy.app.translations.register('review_linked_catalog', {'vi_VN': {('Object', 'Review Linked Source'): 'Vật thể liên kết mẫu'}})
bpy.context.preferences.view.language = 'vi_VN'
bpy.context.preferences.view.use_translate_interface = True
import hashlib
digest = hashlib.sha256(library.read_bytes()).hexdigest()
with bpy.data.libraries.load(str(library), link=True) as (available, loaded):
    loaded.objects = ['Review Linked Source']
linked = loaded.objects[0]
bpy.context.scene.collection.objects.link(linked)
assert linked.library is not None and linked.ui_name_is_translatable
assert linked.name == 'Review Linked Source' and linked.ui_name == 'Vật thể liên kết mẫu'
bpy.ops.wm.save_as_mainfile(filepath=str(directory / 'consumer.blend'))
bpy.ops.wm.open_mainfile(filepath=str(directory / 'consumer.blend'), load_ui=False)
linked = next(obj for obj in bpy.data.objects if obj.name == 'Review Linked Source' and obj.library is not None)
assert linked.ui_name_is_translatable and linked.ui_name == 'Vật thể liên kết mẫu'
assert hashlib.sha256(library.read_bytes()).hexdigest() == digest
```

Inspect a standard item list/Outliner entry too. The library still owns linked items: mark/clear calls on that linked ID raise RuntimeError and ordinary editing restrictions remain. Do not try to fix the displayed name in the file that uses the library by saving the library. Reopening a new process requires re-registering the translation list. [Four actual library tests](../../../../../tests/python/bl_id_ui_name_libraries.py).

## 15. Bring a local copy into your file

Continue with the same library/translation list, or substitute the external example setup's file and source name from section 8:

```python
with bpy.data.libraries.load(str(library), link=False) as (available, loaded):
    loaded.objects = ['Review Linked Source']
appended = loaded.objects[0]
bpy.context.scene.collection.objects.link(appended)
assert appended.library is None
print(appended.name, appended.ui_name_is_translatable, appended.ui_name)
```

If there is no local item with that name, expect the original name and translation permission. If a local item already uses it, Blender adds a number and removes permission from the imported copy. Import another copy to check this. Inspect the actual name, because linked and local items have separate name lists. Rename the first local append to `Review Personal Append`; its personal name and removed permission must survive saving and reopening. Compare the library file checksum before and after. [Append test](../../../../../tests/python/bl_id_ui_name_libraries.py).

## 16. Important check: editable copies of linked items

Use section 14's linked object, with no local item with the same name (start fresh if section 15 already created one):

```python
local = linked.override_create()
bpy.context.scene.collection.objects.link(local)
assert local.library is None and local.override_library is not None
assert local.name == linked.name and local.ui_name_is_translatable
bpy.ops.wm.save_as_mainfile(filepath=str(directory / 'consumer.blend'))
bpy.ops.wm.open_mainfile(filepath=str(directory / 'consumer.blend'), load_ui=False)
local = next(obj for obj in bpy.data.objects if obj.override_library is not None and obj.name == 'Review Linked Source')
assert local.ui_name_is_translatable and local.ui_name == 'Vật thể liên kết mẫu'
local.name = 'Review Personal Override'
local.name = 'Review Linked Source'
assert not local.ui_name_is_translatable
bpy.ops.wm.save_as_mainfile(filepath=str(directory / 'consumer.blend'))
bpy.ops.wm.open_mainfile(filepath=str(directory / 'consumer.blend'), load_ui=False)
local = next(obj for obj in bpy.data.objects if obj.override_library is not None and obj.name == 'Review Linked Source')
assert not local.ui_name_is_translatable and local.ui_name == local.name
assert local.override_library.reference.ui_name_is_translatable
```

Repeat from a fresh marked for translation override with `local.ui_name_translation_clear()` instead of the rename/rename-back pair. Save/reopen: translation permission off must not be silently restored from the marked reference. The marked reference itself remains unchanged. Loss of a valid untouched note or restoration of a user-cleared note is a failure. [Override roundtrip test](../../../../../tests/python/bl_id_ui_name_libraries.py), [shared-rule tests](../../../../../source/blender/blenkernel/intern/id_ui_name_test.cc).

## 17. Copies and names ending in .001 or .002

In a fresh disposable file use a local test brush; the real factory brush may be linked and has a separate list of names:

```python
a = bpy.data.brushes.new('Review Collision', mode='SCULPT')
a.use_fake_user = True
a.ui_name_translation_mark()
b = a.copy()
c = a.copy()
b.use_fake_user = c.use_fake_user = True
assert (a.name, b.name, c.name) == ('Review Collision', 'Review Collision.001', 'Review Collision.002')
assert a.ui_name_is_translatable
assert not b.ui_name_is_translatable and not c.ui_name_is_translatable
assert b.ui_name == b.name and c.ui_name == c.name
```

Use the translation list setup from section 20 to give the original a known translation if needed. Rename b personally; still exactly as written. Save/reopen and find again each brush. This tests ordinary `.copy()`; the window-based duplicate/forced-same-name clash test covers actual Blender commands and undo. Appended same-name clashes are section 15. Neither suffix removal nor renaming back restores permission.

## 18. Undo/redo expectations

Use mouse or keyboard actions or explicit `bpy.ops.ed.undo_push(message=...)` checkpoints in a window-based View3D context; assignments made in the Console alone do not promise an undo checkpoint. The existing section 4.6 script supplies the correct context and re-fetches IDs after each undo.

| Scenario | Before | After operation | Undo | Redo |
| --- | --- | --- | --- | --- |
| Rename | marked for translation source/translation | Personal exactly as written/false | Original name + permission + translation | Personal + false + exactly as written |
| Clear permission | True, translated | Same source, without permission and shown as written | True/translated | False/exactly as written |
| Duplicate | marked for translation original only | Original true; copy numbered/false | Copy gone; original true | Copy false again |
| Forced same-name clash | Two explicitly marked names | Actually changed names false | Original names/permissions restored | Changed names false again |

For manual mark/clear checks, add an Undo step before and after the action. Marking is a deliberate choice by the person supplying the item; matching a familiar spelling must not restore permission. Do not count a menu history listing alone as evidence of the restored values. Verify `.name`, permission to translate and presentation after Undo and Redo. Run before reopening resets Undo history.

## 19. Places to check on screen

| Surface | Expected | Reason/check |
| --- | --- | --- |
| Workspace tab/addition menu | Translated when permission and a translation are available | Sections 5/12 |
| Brush shelf | Translated name/tooltip | Essentials Smooth |
| Brush selector/popover/header | Translated label when permitted | Section 6 |
| Brush tooltip | Translated name | Description text has separate translation list coverage |
| Asset Browser preview/search | Translated label and both-name match | Sections 8/9 |
| Asset tooltip | Translated name | Paths/library references stay saved |
| Registered node-tool menu/F3 result | Translated label, stable tool command name | Section 7 |
| Standard item list | Translated display; language-driven editor | Name Review panel |
| Stored name diagnostic/Python `.name` | Intentionally shows saved text | Finding the item by its saved name |
| Individual node titles, socket names and asset folder names | Intentionally authored exactly as written | Outside the shared ID-name rule |
| Surfaces with no search control | Search not applicable | Do not invent an unsupported search UI |

Tick each applicable row in your evidence. Reading `ui_name` alone does not prove what appears on screen.

## 20. Python commands you can use

Use the supported Python commands below. Do not edit hidden saved notes directly:

```python
item = bpy.data.objects.new('Review API Source', None)
item.use_fake_user = True
print(item.name, item.ui_name, item.ui_name_is_translatable, item.ui_name_translation_context)
assert not item.ui_name_is_translatable
item.ui_name_translation_mark()
assert item.ui_name_is_translatable
bpy.app.translations.register('review_api_catalog', {'vi_VN': {(item.ui_name_translation_context, item.name): 'Tên API mẫu'}})
view = bpy.context.preferences.view
view.language = 'vi_VN'
view.use_translate_interface = True
assert item.name == 'Review API Source' and item.ui_name == 'Tên API mẫu'
item.ui_name_translation_clear()
assert item.ui_name == item.name and not item.ui_name_is_translatable
item.ui_name_translation_mark()
item.name = 'Review Personal API'
assert not item.ui_name_is_translatable and item.ui_name == item.name
bpy.app.translations.unregister('review_api_catalog')
```

`ui_name`, `ui_name_is_translatable`, `ui_name_translation_context` are read-only; assigning to them raises AttributeError. You can still change `.name` when the item is editable. Mark/clear are deliberate actions by the person supplying the item, not a personal language switch. Blender refuses them on linked items and other items that cannot be edited. Each item type supplies its own translation category. [Python name controls implementation](../../../../../source/blender/makesrna/intern/rna_ID.cc), [10 Python commands tests](../../../../../tests/python/bl_id_ui_name.py).

## 21. Check and update supplied files

Approved file list: [15 approved files](../../../../../tools/utils/blend_ui_name_factory_files.json). Standalone mark/extraction check:

```sh
"$B" --background --factory-startup --python-exit-code 1 --python tests/python/bl_id_ui_name_factory.py
```

Expected: three tests pass, all approved local assets already marked with matching source notes, Brush/NodeTree extraction contexts correct, unapproved authoring refused. This reads files and does not save them.

For independent preservation, prepare a separate unchanged original copy at the pre-feature original commit, retaining the `assets/` layout and other linked files. Do not use the already-marked feature files as unchanged original copy:

```sh
BASELINE_DIR="$E/baseline"
git worktree add --detach "$BASELINE_DIR" 0301fc47a65e32a804be6f47187967db2e7a2717
git -C "$BASELINE_DIR" lfs pull
"$B" --background --factory-startup --python-exit-code 1 \
  --python "$P/review/compare_factory_files.py" -- \
  --baseline-dir "$BASELINE_DIR" --output-dir "$E/factory-comparison"
```

Expected `summary.json` passed true: 15 files, 353 brushes and node groups, no recorded differences, unchanged file checksums. Missing LFS content/dependencies fail setup. The comparison checks settings exposed to Python, contained settings, saved notes, previews and the names/types/library files of related items. It leaves out the documented temporary settings, paths and intended translation notes. It does not compare every hidden saved field or every setting inside related items. [Comparison source](compare_factory_files.py), [final limits](../20261003_231111_verification.md).

Optional authoring inspection, for one approved file, marks **memory only** and reports `saved: false`:

```sh
"$B" --background --factory-startup assets/brushes/essentials_brushes-mesh_sculpt.blend \
  --python-exit-code 1 --python tools/utils/blend_author_ui_names.py
```

For a deliberate approved source update, the existing command adds `-- --write-source`; expect `saved: true`. This is a source change, not a verification step. Review its diff and rerun factory mark/extraction and preservation checks. Never run it on user libraries, and never add `--write-source` merely to pass verification. [Authoring script](../../../../../tools/utils/blend_author_ui_names.py).

## 22. Check that Blender still feels responsive

Compare large existing selectors and Browser search in English, Vietnamese, OFF and unmarked cases. Repeated open/filter/hover should show no obvious new delay or duplicate results. Record the file you used and any delay you noticed. This plan does not set a new timing target.

The shared name chooser uses existing text. When an item is unmarked or translation is off, it returns the saved name before looking for a translation. Lists and name editors keep their own text copies where needed. Review these checks in [shared name chooser](../../../../../source/blender/blenkernel/intern/id_ui_name.cc) and run the focused tests. Do not describe a visual timing observation as proof of every memory request or lookup count.

## 23. Names that must stay as written

Create a user workspace with `ws = bpy.context.workspace.copy(); ws.name = 'Review Unmarked Workspace'` (Blender has no `bpy.data.workspaces.new` command), a brush by `bpy.data.brushes.new('Review Unmarked Brush', mode='SCULPT')`, and an object/material with a familiar factory-looking name. Before any explicit mark, all are without permission and shown as written in both languages. Retain them with Fake User (keep an otherwise unused item when saving) if saving unused data.

Repeat with old unmarked Layout/Smooth, a renamed factory item and rename-back. Familiar spelling, asset marking alone and type alone must never allow translation. A different ID type can deliberately allow translation through the shared Python commands; “unrelated type” means an unmarked item, not a type blacklist. Individual nodes and sockets do not have the shared mark command. [Negative/library tests](../../../../../tests/python/bl_id_ui_name_libraries.py), [Python commands tests](../../../../../tests/python/bl_id_ui_name.py).

## 24. What to check when something fails

| Observation | Check first |
| --- | --- |
| Workspace translates, Smooth does not | Correct Blender, installed translation list/Essentials asset, brush permission to translate and translation category, screen label |
| English search text works, translated search text fails | Interface setting, translation list entry, selected library/type, connected translated alternative search name/filter refresh |
| Rename translates again after reload | Clear-note saving and reopening; ensure example setup authoring was not rerun |
| Untouched linked override loses permission to translate | Reference/override transfer during refresh/reload |
| Cleared override regains permission to translate | Local decision overwritten by reference |
| Space replaces the whole name | Initial actual selection/caret, correct rebuilt binary, typing check |
| Select All appears as only a caret | Selection drawing/theme contrast check |
| Python shows a translation but the Browser does not | saved permission note, screen label, first and second reads, and translation list in the running Blender |
| test example falls back after restart | Test translation list not registered; expected unless restored |
| No tests selected / missing factory data | Build/test setup or LFS/resource setup; never a passing test group |

Keep original failures, exact commands and reruns; do not change recorded RED/setup failures to green.

## 25. Expected results at a glance

Search columns refer to supported surfaces and an available translation with Interface Translation ON.

| Representative | Saved name changes with language? | May translate? | User rename exactly as written? | Save/reload? | Source search? | Translated search? |
| --- | --- | --- | --- | --- | --- | --- |
| Workspace | No | Only with permission | Yes | Yes | ID selector/add menu where searchable | Same condition |
| Brush | No | Only with permission | Local copy: yes | Yes | Shelf/selector | Yes |
| Node/tool | No | Only with permission | Editable local: yes | Yes | Registered tool/selector | Yes |
| Asset | No | Only with permission | Local imported: yes | Yes | Browser/shelf | Yes |
| Old user data | No | No without explicit mark | Yes | Yes | Current stored name | No added translated search name |
| Renamed data | No | No | Yes | Yes | Current stored name | No former alternative search name |
| Linked data | No | Saved valid permission | Direct editing restricted | Yes | Supported surface | Available entry |
| Override | No | Valid unchanged permission | Yes; stays cleared | Yes | Supported surface | While still marked for translation |

## 26. Reviewer sign-off

- [ ] Focused automated tests pass; zero omissions/skips.
- [ ] 40 related program checks and seven Python test groups pass.
- [ ] Workspace and real Sculpt brush checked on screen.
- [ ] Registered node-tool and Asset Browser checked on screen.
- [ ] Both-name search and switching language and translation on/off verified.
- [ ] Rename, rename-back, typing and visible selection verified.
- [ ] Save/reload, copy/same-name clash and undo/redo verified.
- [ ] Link, append, override and legacy/unmarked behavior verified.
- [ ] Factory saved marks/extraction and preservation verified.
- [ ] No unexpected stored-name change.
- [ ] Commit author/committer use the human identity; no prohibited credit trailers.

```sh
git config user.name
git config user.email
git show -s --format=fuller HEAD
git log --reverse main..HEAD --format='%H %an <%ae> | %cn <%ce>%n%B'
```

Expected author/committer: Hoang Duy Tran <hoangduytran1960@gmail.com>. Review all feature commits, not upstream history. Record reviewer, date, checkout/build hashes, pass/fail/not-run per test group, exact result file paths and any genuine blockers.

## 27. Results, references and limits

[Reviewer README](README.md), [authoritative verification](../20261003_231111_verification.md), [current document index](../20261003_231111_generic-name-localization-design.md#current-status-and-document-index), [historical evidence index](evidence/README.md), [final independent implementation review](evidence/20261004-destination/external-browser-final-auditor.md).

The source/test links above identify the checks that can be run for each area. Dated reports preserve earlier failures and limitations. Visible results in final verification came from user screenshots/manual confirmations; JSON/Python commands checks are not screenshots. The final external/typing confirmations have a written manual record, not an invented capture.

The commands were checked against the current scripts and recorded successful runs. Counts were checked against the current test lists, approved files and final reports. New Python examples were run in the rebuilt Blender. An independent review checked the steps against the code, design, tests and reviewer README. This plan covers the requested main and related checks, not every Blender test or every possible build. Looking at screen labels, tooltips and highlighting, judging responsiveness, and making a file with an older Blender still require a reviewer.

### Checks made before publishing this plan

The new Python examples passed eight checks in the rebuilt Blender, including save/reopen, linked items, imported copies, editable linked copies and numbered brush copies. The corrected build-identification command passed. Current test lists contain 77 main checks, 37 related checks and three search checks. CTest lists all seven requested Python groups. Six runner self-checks passed. All 56 existing local links and 29 code blocks were checked; the new links below also resolve. Existing reports confirm nine reviewer checks and 15 files/353 items.

The first draft used a class-property check and a workspace creation command that Blender does not provide. Both instructions were corrected and checked before publication. A failed setup attempt in the separate validation script is retained apart from the passing results. No failed result was relabeled as success. The entire long-running test plan was not rerun for this document-only change.

[Independent plan review](evidence/developer-plan-review/independent-review.md), [eight example checks](evidence/developer-plan-review/python-examples.json), [example-check log](evidence/developer-plan-review/python-examples.log), [file-setup and missing-entry checks](evidence/developer-plan-review/file-and-fallback-examples.log).
