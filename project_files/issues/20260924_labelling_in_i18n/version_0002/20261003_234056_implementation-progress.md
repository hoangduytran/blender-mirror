**Historical record:** this describes the first implementation stage. The current code and completion checks are documented in [verification](20261003_231111_verification.md) and [implementation](20261003_231111_implementation-analysis.md).

# First implementation: shared translated names

**Date:** 2026-10-03, Europe/London. **Status:** first shared stage implemented and independently tested; wider feature remains unfinished.

Branch: `feature/generic-ui-name-translation`, from local `main` at `0301fc47a65e32a804be6f47187967db2e7a2717`.

> Historical record for the original checkout. Current port/build evidence: [reviewer plan](review/README.md).

## The agreed first step

Make explicit author-marked names work through one shared helper, without changing saved-name editing. Connect workspace tabs/addition menus and the existing asset menu. Keep the change compact; no new feature libraries or naming system.

## Code already written

- Blender architecture: existing DNA structures hold storage; RNA exposes checked actions and read-only labels; `bpy` uses those RNA APIs.
- Existing system-property storage holds `{version: 1, source: original name}`.
- Existing asset properties hold a derived listing copy; one checker interprets both.
- Real name changes clear the note; unchanged names keep it. Copying checks the final name after the note is copied.
- Author actions: `ID.ui_name_translation_mark()` / `ui_name_translation_clear()`.
- Read-only information: `ID.ui_name` / `ui_name_is_translatable`.
- Tabs use the same label for width and drawing. Import references and rename fields keep the saved name.
- Startup/addition no longer translate saved workspace names. Factory marks are still outstanding.
- New conditions use meaningful boolean names. Pointer checks and text checks still stop early when not needed.

## Test-first record

The initial source edits began before the user added the TDD instruction. Do not describe those edits as test-first.

An independent tester then wrote real tests and ran the Python suite on installed Blender 5.3 Alpha (`cac54124d225`). Eight tests fail with the expected missing author-action assertion. That establishes missing functionality; it does not prove every later regression was reproduced independently.

The tester prepared malformed-property and invalid-text tests before the corresponding next fixes. The rebuilt C++ test executable now passes those cases.

- Actual baseline RED log: `/private/tmp/id-ui-name-official-baseline-red.log` (the current recorded run has all eight cases).
- Workspace append fixture checked separately on installed Blender; saving a copy and appending with a name clash works.
- Existing reference examples: 26 pass; these remain separate from Blender runtime checks.
- Independent syntax-only checks passed for initial core source and tests. Final linked/runtime checks pass: 26 new C++ +20 nearby existing checks and all 8 Python checks.

## Build repair

The old build could not start because it pointed to a missing Homebrew OpenImageIO library and an unavailable Xcode SDK. The project’s existing bundled libraries are present.

Temporary Ninja provides tooling already required by Blender. CMake now uses the installed Command Line Tools SDK and the bundled packages, including the existing OpenXR dynamic loader instead of a stale static-library path. C++ tests were enabled using Blender’s existing Google Test dependency. No new feature libraries were added.

Build directory: `../build_darwin_full`. Building `blender` and `blender_test` requires a broad rebuild because old compile/library settings changed.

## Close this step only when

- [x] Blender and the test executable compile; app resources installed.
- [x] Independent C++ and Python tests pass on the built branch.
- [x] Nearby rename/asset tests pass.
- [x] Auditor reviews frozen source and DNA/RNA/bpy layering; documents agree with source.
- [x] Feature code committed as `68fb0ffe0a0`; documentation is in its separate companion commit. Existing Console edits are excluded.

## Later work, not claimed complete

Reviewed factory marks, generic translator collection, asset-browser/search/sort labels, remaining duplicate/brush import paths, actual screen/several-window checks, and older-reader limits.

## Final evidence

46 C++ checks (26 new, 20 existing) and 8 actual Blender Python checks pass independently. The 26 reference-model checks also pass. Logs and exact commands are in the verification document. No AddressSanitizer or new screen checks were run.

The additional brush-renaming experiment also passed, showing marked translation, personal rename clearing, `.blend` save/reopen, and literal rename-back through existing DNA/RNA/bpy APIs.

The node-renaming example passed independently on 2026-10-04: node lookup/name/custom-title/type persistence, NodeTree opt-in and rename clearing, and unchanged custom socket names. No production changes; diagram rendered and inspected.

Additional user-requested examples pass independently: materials, objects, collections, actions, asset metadata and four contained-name fields. These are RNA/file checks; no production changes or wider screen integration.
