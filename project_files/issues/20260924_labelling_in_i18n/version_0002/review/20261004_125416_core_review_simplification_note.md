# A smaller approach to translated display names

For Blender developers to consider. Based on the working, tested prototype at `cfab01335e3` in the original branch and `33b50b76082` in the second checkout. This note proposes changes for discussion. It does not change the implementation or replace its verified design, results or test plan.

## Current implementation and this note

The design, implementation explanation and verification describe the completed, tested code. This note describes possible reductions for a later code change. The node-tool yes/no replacement below is feasible as a small change in this patch, but it has not been applied. The saved-flag alternative also remains a proposal for core review.

Before removing `BKE_id_ui_name_properties_copy()`, replace its production callers in `node_group_operator.cc` and its test callers in [id_ui_name_test.cc](../../../../../source/blender/blenkernel/intern/id_ui_name_test.cc) and [wm_operator_type_test.cc](../../../../../source/blender/windowmanager/intern/wm_operator_type_test.cc). The tests must still check that the tool keeps valid name information after the original item or asset listing is released.

Any such code change needs fresh tool-registration, language-switching and external-asset checks. Today's passing counts describe today's copied-note implementation. This documentation update leaves production code and test behavior unchanged.

## The recommendation

Keep the shared name rule. Ask Blender core to choose how permission is saved before polishing the whole patch for submission. The strongest alternative is a saved yes/no flag, followed by a smaller yes/no copy for unloaded assets and node-tool labels. Review the name-editing changes separately so the size of that work does not hide the smaller name rule.

Do not rewrite the working prototype yet. It shows that the rule works across workspaces, brushes, node tools and assets. Its tests and earlier failures are useful evidence for whichever saved form Blender chooses.

## What must stay

1. Keep the normal saved name, `ID.name`, as the name used to find the item.
2. Translate only what people see, using the current language.
3. Require explicit permission. A familiar name, an asset mark or a workspace is not permission.
4. Remove permission after a real personal rename. Renaming back must not restore it.
5. Show the saved name when translation is off or unavailable.
6. Keep source-name and translated-name search where the current implementation provides them.
7. Preserve the rule through copies, clashes, Undo/Redo, saving, reopening and library use.
8. Let an unloaded asset carry enough information to show a label without importing it or changing its source file.

The three possible displayed results remain default, translated and personal. A saved three-state choice is not needed.

```text
saved name + permission to translate + chosen language/available entry = displayed name
```

## 1. Replace the full permission note with a saved flag, if core agrees

The current note stores a version and a copy of the name inside `ID.system_properties`. That name copy lets Blender reject an old note when the actual name no longer matches. It is a safety check, not a second editable label.

A proposed flag such as `ID_FLAG_UI_NAME_TRANSLATABLE` would say only “this name may be translated.” That symbol does not exist in the current implementation. Setting it would be an explicit author action; a user rename would clear it. Language changes would leave the flag and name alone.

| Choice | What becomes simpler | What still needs work |
| --- | --- | --- |
| Keep the tested note | No new saved flag; current matching-name protection remains | Keep note checks and note copying |
| Use a native saved flag | Remove the version/name note and its group handling; permission becomes one yes/no check | Agree the saved meaning, old-file handling, rename/copy rules, assets and overrides |

**Where to start:** [DNA_ID.h](../../../../../source/blender/makesdna/DNA_ID.h#L436) already describes `ID.flag` as saved and `ID.tag` as temporary. A suitable bit in the existing saved field might avoid changing the structure's size. It still changes the meaning of saved data and needs core review. Do not use a temporary tag, select a numeric bit just because it appears free, or assume every old file stored it as zero. Check historical bit use and the relevant old-file conversion rules first.

Also inspect [readfile.cc](../../../../../source/blender/blenloader/intern/readfile.cc), [writefile.cc](../../../../../source/blender/blenloader/intern/writefile.cc) and the version-conversion files under `source/blender/blenloader/intern/`. Saving and reading must preserve the intended bit. Files from before the feature must not acquire permission accidentally. Decide whether files from this private prototype need conversion; do not ship two permanent sources of permission merely to avoid making that decision.

### Concrete removals and reductions

The implementation below is in [id_ui_name.cc](../../../../../source/blender/blenkernel/intern/id_ui_name.cc). Public BKE entry points are declared in [BKE_id_ui_name.hh](../../../../../source/blender/blenkernel/BKE_id_ui_name.hh); the `descriptor_*` helpers stay private to the implementation file.

| Current place | Proposed change with a native flag | Keep |
| --- | --- | --- |
| `descriptor_key`, `descriptor_version`, `descriptor_get()` | Remove this saved-note format once its use has been replaced | Any required one-time conversion of prototype files |
| `descriptor_matches()` | Remove version/type/length checks, copied-name comparison and repeated UTF-8 checks for the note | Safe handling of the actual name and its normal storage rules |
| `descriptor_remove()` | Remove group lookup/freeing; clear the approved bit instead | Clearing only translation permission, leaving other saved properties alone |
| `BKE_id_ui_name_is_translatable()` | Read the bit instead of looking through a property group | One common permission query for all callers |
| `BKE_id_ui_name_mark()` | Remove creation of the version/source property group | Editable/local-item checks and deliberate authoring |
| `BKE_id_ui_name_clear()` | Clear the bit instead of deleting the note | Refresh of asset information and visible labels |
| `BKE_id_ui_name_resolve()` | Accept a yes/no permission value, rather than knowing the property-group format | Current language check, type-specific translation category and safe default |
| `BKE_id_ui_name_properties_copy()` | Remove if node tools no longer copy property groups for their names | A small owned record of the tool's current source name and permission |
| `BKE_id_ui_name_copy()` / `BKE_id_ui_name_copy_finalize()` | Remove their note-allocation/checking parts; reconsider the helper shape | Final-name checks and correct permission transfer/clearing |

This is a conditional removal list, not permission to delete those helpers now. A flag does not prove that a copied name stayed unchanged. The current name-copy guard catches some missed rename paths automatically; a plain bit does not. Before removing it, check every path that writes or finalizes a name, including names changed by clashes.

In particular, retain the decisions at [lib_id.cc](../../../../../source/blender/blenkernel/intern/lib_id.cc#L878): user copies clear permission; copied/imported items use their final names; actual renames clear permission on every changed item. The current calls around `BKE_id_ui_name_copy_finalize()` and the rename clash branches must be replaced with equivalent rules, not simply removed.

## 2. Shrink the node-tool name record even if saved storage stays unchanged

This is a smaller experiment which need not wait for the flag decision.

`OperatorTypeData` already owns its source name. It also owns an extra property group just for translation permission. In [node_group_operator.cc](../../../../../source/blender/editors/geometry/node_group_operator.cc#L141), consider replacing `name_translation_properties` with one copied yes/no value, validated when the tool is registered.

| Exact place | Reduce/remove | Preserve |
| --- | --- | --- |
| `OperatorTypeData::name_translation_properties` | Replace the allocated property group with a yes/no member | The already-owned source name |
| `OperatorTypeData::from_asset()` and `from_group()` | Validate permission once, then store its result instead of cloning the note | Reading an unloaded asset without importing it |
| `OperatorTypeData::ensure_hash()` | Compare/hash that yes/no value instead of the copied group | Refresh when a rename, permission change, Undo or file read changes the tool |
| `node_tool_display_name()` | Pass the source name and copied permission to the common name chooser | Choose the translation when displaying, not at registration time |
| `BKE_id_ui_name_properties_copy()` | Remove this helper if these are its last callers | Proper freeing/ownership of any other tool settings |

This needs a narrow shared function which accepts an already-checked permission value. Loaded-item callers would still obtain their permission through the normal checked helper. The copied yes/no value must be refreshed on the same events as today's record; it must not outlive an unnoticed rename.

Do not remove `asset_meta_data_properties`. It holds the tool's input settings and is separate from the name permission copy. Deleting both would break more than name translation.

## 3. Keep unloaded-asset support, but reduce the information carried

[AssetRepresentation::get_display_name()](../../../../../source/blender/asset_system/intern/asset_representation.cc#L142) chooses the loaded item's name rule when the item is loaded and uses saved asset information otherwise. Keep that distinction.

In [BKE_id_ui_name_asset_sync()](../../../../../source/blender/blenkernel/intern/id_ui_name.cc#L119), a native-flag version could replace the copied version/source group with a saved yes/no asset value. There is already a source name in the asset listing; another source-name copy need not be required after the safety rules are agreed.

That asset value is a copy for browsing, not a second authority. Marking and clearing, renaming, asset creation and saving must keep it correct. A loaded item remains authoritative. The source file is not rewritten merely to display another language.

Before choosing an existing-property boolean or a native asset flag, review [DNA_asset_types.h](../../../../../source/blender/makesdna/DNA_asset_types.h), the asset file-reading paths and [filelist.cc](../../../../../source/blender/editors/space_file/filelist/filelist.cc). The saved search index must not keep an old permission value after the asset changes. A simpler value still needs a refresh/conversion rule.

Keep the actual first-read/second-read Browser test. It proves that source and translated search find the same unloaded item and that browsing imports nothing. Changing the storage does not make this test unnecessary.

## 4. Separate name-editing work from the smaller display-name proposal

The current implementation starts name editing with the selected-language text. Esc and unchanged Enter keep the original saved name; an actual edit saves personal text and removes permission. Longer translations fit, Space appends at the cursor, and selected tab text is visibly highlighted.

These are required behaviors of the completed prototype. Moving their code to another patch is different from removing the behavior.

| Physical place | Put in a separate name-editing/UI patch | What would be lost if merely deleted |
| --- | --- | --- |
| [interface_intern.hh](../../../../../source/blender/editors/interface/interface_intern.hh#L941): `ButtonIDNameEdit` | Temporary remembered display text and edit-owner declarations | Correct comparison of changed versus untouched translated text |
| [interface.cc](../../../../../source/blender/editors/interface/interface.cc#L3535): `button_id_name_edit_begin()` / `apply()` | Start/apply rules and longer edit text | Selected-language editing, safe Esc/Enter and correct personal rename |
| [interface_handlers.cc](../../../../../source/blender/editors/interface/interface_handlers.cc#L3908) | Edit record use, buffer handling and initial selection choice | Space/cursor behavior; protection against replacing the whole name unexpectedly |
| `edits_workspace_name` / `starts_unselected` in the same handler | The workspace's initial cursor rule | Personal workspace names could start selected again |
| [interface_widgets.cc](../../../../../source/blender/editors/interface/interface_widgets.cc#L2660): `widget_text_selection_color()` use | Visible tab selection correction | Selected text could look like an unselected cursor again |

The workspace-specific cursor check is an editing choice, not part of deciding whether any name may translate. Present it that way. It has a reason: the user found replacement and invisible-selection problems. Do not quietly return to English-only editing or remove the Space/highlight fixes to make a patch appear smaller.

If core wants to review display names before deciding name-editing behavior, submit clearly separate patches and say which behavior depends on the second patch. The finished result still needs both. This reduces review size, not necessarily total code size.

## 5. Reconsider the operator-wide name switch, without breaking existing tools

The new `wmOperatorType.name_requires_properties` is declared in [WM_types.hh](../../../../../source/blender/windowmanager/WM_types.hh#L1191). It protects existing name functions which need tool settings, while allowing this node tool to resolve a label with no settings pointer. It defaults to the existing safe behavior.

The affected uses are [WM_operatortype_name()](../../../../../source/blender/windowmanager/intern/wm_operator_type.cc#L601), [operator search](../../../../../source/blender/editors/interface/templates/interface_template_search_operator.cc#L62), and [register_node_tool()](../../../../../source/blender/editors/geometry/node_group_operator.cc#L1437).

Ask core to choose between:

- Keeping this small, general distinction in a separate WindowManager review, with tests proving existing name functions are not called without their required settings.
- Finding an existing safe presentation path that can show node-tool labels everywhere needed without extending the operator-wide type. Only then remove the field, its condition in `WM_operatortype_name()`, the node-tool assignment and the operator-search branch that relies on it.

The second choice is a question to investigate, not a working replacement supplied by this note. Do not just call every existing name function with a null pointer. Do not hard-code workspace/node-tool cases into the shared name chooser. Do not translate `ot->name` once when registering the tool: it would go stale when language changes. A replacement must still support both search names, literal unmarked tool names and unchanged command identifiers.

Changing a tool's translation category alone is also insufficient: it does not represent explicit permission or guarantee literal unmarked names. A new alternative display function would still be an operator-wide API decision, not proof that the cost vanished.

## 6. Keep search, reduce avoidable repeated work only where measured

In [interface_template_id.cc](../../../../../source/blender/editors/interface/templates/interface_template_id.cc#L175), `BKE_id_ui_name_search_text()` joins the saved name and a distinct translation for existing search. Its other selector use is nearby. In [id_ui_name.cc](../../../../../source/blender/blenkernel/intern/id_ui_name.cc#L98), unchanged display text already uses the single-name path.

Consider separate source/display search keys only if the existing search code can attach both to one item and return it once. Otherwise the current short join is a reasonable small solution. Keep translated search off when translation is off; do not retain old translated matches after a language change.

The current resolver avoids translation calls when the setting is off or the note does not match. A native bit or a checked tool permission value would reduce property lookups and repeated note checks on the translation-enabled path. That is a clear reduction in work, but there is no measured speedup claim here.

Do not add a new global translation cache as a supposed simplification. It would need rules for language changes, rename, Undo, reopening and changed external files. Measure selector/search time before taking that extra work on.

## 7. Do not remove override, copy or factory rules along with the note

The relevant override calls are in [lib_override.cc](../../../../../source/blender/blenkernel/intern/lib_override.cc#L333), including `BKE_id_ui_name_copy(*tmp_id, *local)` during refresh. An untouched marked reference may supply permission to a new override. A locally cleared or renamed override must keep that decision after refresh and reopening.

A native bit can reduce transfer to a yes/no operation. It cannot erase the distinction between those two cases. Generic copying of the reference's flags is not enough if it restores permission the user deliberately removed.

Keep explicit supplied-file authoring in [blend_author_ui_names.py](../../../../../tools/utils/blend_author_ui_names.py) and its [approved file list](../../../../../tools/utils/blend_ui_name_factory_files.json). A flag does not know whether a file is trusted factory content. Do not mark all assets at startup or infer permission from Smooth/Layout spelling.

The public name actions in [rna_ID.cc](../../../../../source/blender/makesrna/intern/rna_ID.cc#L775) can keep the same outward behavior even if their saved form changes. Blender's saved fields remain below the checked name actions, which are then exposed to Python. Do not add direct Python access to unchecked flag writes just to reduce wrapper code.

## 8. Which tests may shrink, and which must remain

If the version/source note is removed entirely, its format-specific tests in [id_ui_name_test.cc](../../../../../source/blender/blenkernel/intern/id_ui_name_test.cc) can be removed or replaced: wrong version, wrong property types, malformed copied-name storage and stale-note matching no longer describe a native bit. Any supported conversion of prototype notes needs its own checks.

Keep the behavior tests: explicit marking, old/unmarked names, real rename, rename-back, user copy, final-name clashes, override refresh, linked ownership, save/reopen, both-name search, unavailable translations and runtime language switching. Keep [registered tool and Browser tests](../../../../../source/blender/windowmanager/intern/wm_operator_type_test.cc), [library tests](../../../../../tests/python/bl_id_ui_name_libraries.py), [actual Sculpt test](../../../../../tests/python/bl_id_ui_name_sculpt.py), and the editor/typing/Undo tests when those changes remain in the submitted set.

Do not promise the present 77-case count for a different implementation. Record the new expected case list and keep the same behavioral coverage. Removing checks just to make a changed implementation pass is not a reduction in design complexity.

The [developer test plan](DEVELOPER_TEST_PLAN.md) and [final verification](../20261003_231111_verification.md) describe today's implementation. Update them if an alternative is actually adopted. Until then, keep this note clearly separate from current implementation claims.

## A practical review order

1. Agree the small name rule and the explicit author/user distinction.
2. Choose the saved permission form. Prefer exploring an approved native flag; keep the tested note if its safety/compatibility benefits outweigh the extra checks.
3. Try the smaller node-tool name record, without changing language-switch behavior.
4. Review the unloaded-asset copy and override/copy decisions together with that storage choice.
5. Review operator-name plumbing separately; remove it only after an equally complete safe path is demonstrated.
6. Review the selected-language editor and cursor/highlight fixes as a separate patch.
7. Run the same behavior checks against the final combination before submission.

This gives Blender reviewers a smaller central proposal and precise places to reduce its implementation, while preserving the evidence and behavior already achieved.

[Independent note review](evidence/core-review-note/independent-review.md). The requested distinction between private helpers and public declarations has been corrected. No production code or test behavior changed.
