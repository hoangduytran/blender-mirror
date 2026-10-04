# Translate supplied tool names without changing saved names

Updated 2026-10-04. Implementation, required focused and nearby verification, and required visible checks are complete. Both feature branches are synchronized. No required blocker remains. This is a proposal for core review, not upstream approval. See [verification](20261003_231111_verification.md).

The reviewers asked for a general solution covering workspaces, brushes, node groups used as tools, and assets. The same saved name can be both a file identity and a label people read. Translate the label only. Leave file identity and normal renaming intact.

## Current status and document index

The local implementation is complete and verified for the agreed scope. Blender core approval is a separate review decision; this design remains a proposal.

| Purpose | Document |
| --- | --- |
| Current authoritative design | [This design](20261003_231111_generic-name-localization-design.md) |
| Current implementation description | [Implementation and exact code](20261003_231111_implementation-analysis.md) |
| Current verification | [Final verification](20261003_231111_verification.md) |
| Reviewer instructions | [Commands](review/README.md) and [step-by-step developer test plan](review/DEVELOPER_TEST_PLAN.md) |
| Alternatives for core discussion (not implemented) | [Smaller approach and exact code locations](review/20261004_125416_core_review_simplification_note.md) |
| Commit identity verification | [Identity and commit maps](20261004_121634_commit_identity_verification.md) |
| Historical implementation record | [Earlier progress](20261003_234056_implementation-progress.md), superseded by final verification |
| Historical pause record | Historical sections of [RESUME_STATE.md](RESUME_STATE.md); its opening completion state is current |
| Historical test and review snapshots | [Evidence index](review/evidence/README.md); earlier failures and reservations remain unchanged |

## What is in the code today

The verified code still saves a permission note containing a version and the source name. A node tool keeps its own source name and a checked copy of that note. It chooses the displayed text using the language selected at the time it is shown.

The [smaller-approach note](review/20261004_125416_core_review_simplification_note.md) describes possible next changes. Replacing the node tool's copied note with one yes/no value has **not** been done. Replacing the saved note with a flag has **not** been done either. Neither suggestion is included in the recorded passing results. This documentation update changes no code, saved files or test behavior.

## One compact rule

```text
saved ID.name + explicit author permission + current language/catalog = displayed name
```

`USE_DEFAULT`, `USE_TRANSLATION`, and `USE_USERDEFINE` describe the three possible results. They are not saved states and there is no three-state enum. A user rename removes permission. Without permission, show the saved name. With permission and Interface Translation enabled, show the available translation; otherwise show the saved name.

Permission is a small existing-property note containing a format version and the exact source name. Blender checks the note against the current name and uses the existing translation context for that kind of item. Familiar spelling, being an asset, and membership of a workspace are never permission. A personal brush called “Smooth” stays “Smooth”.

Factory startup workspaces are marked in the trusted startup update. Reviewed bundled asset files receive saved marks through an explicit file manifest and authoring script. Opening an ordinary file or appending a workspace never invents permission. Old files therefore remain literal.

## Everyday behavior

| Action | Result |
| --- | --- |
| Switch language or disable Interface Translation | Change the presentation; never rewrite `ID.name`. Missing translations fall back safely. |
| Rename an item | Show the final stored name literally and remove permission when the name actually changes. |
| Rename back | Keep it literal. Only an explicit author action can restore permission. |
| Cancel an edit or confirm unchanged text | Keep the original saved name and permission. Edit fields start with the current displayed name in the selected language. Workspace names always start with an unselected caret at the end, including saved personal names; translated editors for other IDs do too. Space then appends; Select All still permits replacement and must show a visible highlight. |
| User duplicate or collision adds `.001` | The new item is literal. Normal uniqueness rules still apply. |
| Undo/redo | Restore name and permission with existing Blender undo; refresh tool registration snapshots. |
| Save/reopen | Save source name and permission; derive the label again in the current language. |
| Link, append, or make a library override | Keep existing library editing rules. Preserve valid permission when identity/name survives; clear it after a real name change. Override refresh preserves the local rename decision. |
| Browse an external asset | Resolve its saved metadata before import. Paths, weak references, operator identifiers and raw lookup names stay stable. |
| Search | Match source and displayed names, returning each item once. Translation off removes the translated alias. |
| Several items share a translated label | Keep separate identities. Existing source/library details distinguish them. |

## Use Blender's existing layers

DNA stores the existing `ID.name`, `ID.system_properties`, and asset metadata structures. There is no new DNA field or file-format version. BKE owns validation, resolution, note copying, and rename policy. RNA exposes read-only `ui_name`, `ui_name_is_translatable`, and `ui_name_translation_context`, plus explicit author mark/clear actions. `bpy` exposes those RNA APIs. UI callers use the shared BKE/RNA presentation and existing search mechanisms.

The main note is stored in `ID.system_properties`. Asset metadata holds a derived copy for browsing before import. Importing the whole item restores the main note as authority. Node-tool registration owns a minimal snapshot containing only that note; it refreshes after relevant edits, undo and file reads. It does not scan all IDs or import assets to draw a label.

## Included presentation areas

Workspace tabs and addition menus; brush headers and asset shelves; node-group labels and registered node-tool menus/search; Asset Browser previews/search/tooltips; generic ID selectors and read-only ID-name fields; UI lists, breadcrumbs and ID Outliner entries. Drawing and width measurement use the same text. Editing begins with the current presentation. The temporary edit session remembers the original source and displayed text: unchanged confirmation keeps the source; a real edit saves the user’s text literally. File paths, ordinary node/socket titles and canonical operator names keep their existing meaning.

Resolution borrows the stored name or catalog text, without allocation. Longer-lived UI records and active edit sessions copy text they own. Search builds aliases only where existing search already needs owned keywords. No new project libraries are required.

## Limits and review decisions

Core still needs to approve the opt-in API, storage convention and reviewed factory scope. Existing translations may not cover every newly marked asset name: the extractor now supplies marked names in their ID translation context, and untranslated names fall back to source. This feature does not translate node instance titles, socket names, asset tags/descriptions/catalog paths, or create new undo support. It does not guess the history of old names or add a second personal display-name field.

See [implementation and exact code](20261003_231111_implementation-analysis.md), [reviewer scripts](review/README.md), and [diagrams](diagrams/README.md). Automated data checks and visible application checks are reported separately.

Editing clarification, 2026-10-04: the user rejected revealing the English source on double-click while Vietnamese is selected. The above language-driven edit rule supersedes the earlier raw-source editor. Its implementation and renewed checks are complete, including Space appending and visible selection; no extra saved name or enum is introduced.
