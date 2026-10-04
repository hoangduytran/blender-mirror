# Feature completion state

All required implementation, automated tests and visible user checks pass. Both source branches are synchronized and built. Final Browser coverage: 77 focused C++, nine reviewer checks and six runner self-checks in each checkout. Earlier identical-production gates also pass: 40 broader/search, seven Python suites, 14 typing variants, three undo checks and 15-file/353-ID preservation. No required user input remains.

Latest production correction 9d6c903c247 / destinationd8735998d4e; latest Browser testd72f0ad5721 / destinationb15865455c8. No new production change was needed after resume. Exact final evidence and remaining limits are in 20261003_231111_verification.md. The historical pause snapshot below is retained for traceability only; it does not describe current status.

Commit identities were corrected to Hoang Duy Tran <hoangduytran1960@gmail.com> in both local feature branches. Only feature commit metadata changed; every recorded test still describes the same code. Historical logs and pause notes retain the hashes from their original runs. Old-to-new maps are in `review/evidence/20261004-authorship/`. Upstream history and the unrelated Console edit remain unchanged.

# Historical pause snapshot

Saved 2026-10-04 03:26:20 BST. User instruction: **agent, stop, save states, resume later**. Do not resume implementation, tests or porting until requested. Feature is not complete.

## What to investigate next

The user answered the final external Asset Browser question: **The label or search is wrong**. This is a real remaining failure, not a passing check. Exact symptom is not yet known. A clarification was asked: is the label English, the asset absent, or the translated query failing? It has not been answered. Investigate actual external FileList/Asset Browser display and filtering; shared external metadata/keyword tests pass but do not prove this UI path. Use TDD for the discovered symptom.

The current personal-name Space and visible Cmd+A highlight question also remains unanswered. Do not reuse earlier narrow “it works” as confirmation of the newest correction. Computer Use still rejects Blender; do not bypass the app gate with operating-system UI tools.

## Saved repositories and builds

Original: `/Volumes/1TB_BK/hoangduytran/Dev/tran/blender-git/blender`, branch `feature/generic-ui-name-translation`, HEAD `c02ec921455`. Latest source correction `cc681e66a7e`; preceding design/evidence `9e03ec5de82`. Build `../build_darwin_full`, installed app `bin/Blender.app`. Built/tested tree contains the source correction after older HEAD4041af919a4; binary version hash reports4041af919a44. The unrelated existing Console edit remains uncommitted and must be excluded from feature commits and port.

Destination: `/Volumes/1TB_BK/mini_sequoia/Dev/programming/blender_stuff/blender` resolves to `/Volumes/1TB_BK/hoangduytran/Dev/programming/blender_stuff/blender`, branch `feature/generic-ui-name-review`, HEAD `ec9a9b566ef`. Source equivalent `386044ce923`. Release `../build_darwin` install+blender_test build passed. Original final evidence commit `c02ec921455` and this pause record have **not** yet been ported; source/test/assets are synchronized. Do not start another branch or rewrite main.

All72 feature source/test/script/asset files match between checkouts. Full mapping through source/design correction is retained in `review/evidence/20261004-destination/selection-final-commits.json`.

## Completed checks in both checkouts

- Release install and focused-test builds exit0.
-76 focused C++ cases, including7 editing/color cases; zero failure/error/disabled/skips.
-40 broader/search C++ cases (37+3).
-All9 reviewer checks: API10, libraries4, factory/extraction3, real Sculpt1, examples3, reference26.
-All7 existing Python suites eventually pass. Initial seventh helper abort and exact successful root rerun are retained separately; do not relabel initial failure as success.
-Actual native typing7states×2controls =14variants passes Space/Đ input, Esc and unchangedEnter. Test uses exact macOS Metal/window flags, isolated resources, normal header redraw; unsafe synchronous redraw experiment removed.
-Actual foreground undo3 passes rename, duplicate and forced-collision undo/redo.
-Factory read-only comparison15files/353IDs passes with documented exclusions.
-Independent final source/evidence audit passes72matchingfiles, code excerpts and DNA→BKE→RNA→bpy→UI consistency. It explicitly does not claim pixels or actual external FileList filtering.

Original results: `/private/tmp/ui-name-selection-final-original-review/run-l9pa4uzr`, direct typing `/private/tmp/ui-name-final-events-root-rusct82v`, undo `/private/tmp/ui-name-final-undo-gt4n91hg`, factory `/private/tmp/ui-name-final-factory`, final seventh helper `/private/tmp/ui-name-final-idprop-u54y0_u1`.

Destination results: `/private/tmp/ui-name-caretfinal-destination-review/run-dgsx194h`, native typing/undo/factory `/private/tmp/ui-name-caret-final-destination-native-eut5_tfo`, final seventh helper `/private/tmp/ui-name-caret-destination-idprop-ijhmm1sv`. Buildlog `/private/tmp/ui-name-caret-destination-build.log`. Committed evidence in both `review/evidence/20261004-*` folders.

## Editing correction and constraints

Every workspace editor starts with an unselected end caret, including personal, unmarked, OFF, English and missing-entry names. Distinct translated other-ID editors start unselected too; ordinary other literal-ID selection convention stays. Both tab selection draw paths reuse existing text-field highlightRGB, keepalpha51 and obtain theme lazily only for a selectedTab. Real edits clear eligibility; Esc/unchangedEnter preserve source. No persisted three-state enum, newDNAfields or libraries.

Stored ID.name + explicit eligibility + current locale/catalog derive presentation. Language never rewrites source. Renaming back never restores eligibility. Tight compact code; meaningful boolean vars before if and lazy evaluation; ordinary-English documents, actual code excerpts, Mermaid diagrams; TDD. Keep unrelatedConsole untouched.

## Actual manual evidence already obtained

Real Sculpt Smooth→Làm Mịn header/shelftooltip, Layout→Bố Trí, translationOFF/ON; registered node-tool F3 translated presentation with source query; personal node-tool rename and rename-back literal, undo/redo translated/literal; node personal save/reopen; CurrentFile Asset Browser translated asset, bothsource Review and translated Tài nguyên searches one result; held translated query disappears inEnglish and returns inVietnamese. User reports personal workspace save/reopen works. New highlight/personalSpace confirmation stillpending; external final check now explicitlyfails. Vietnamese typing/input-method limitation excluded by user.

## Running review instance

Root native session58999 launched original app with `--factory-startup --python tests/python/bl_id_ui_name_gui.py -- --output-dir /private/tmp/ui-name-final-visible-review --with-external-library`. This isolated review registers library **Name Review External**, English source **Review External Asset Source**, supplied Vietnamese **Tài nguyên ngoài mẫu**. Do not import the asset during pre-import search check. User may close it; do not terminate or alter their other unsaved instance. Build/tests have completed; no test/build work is intentionally left running.

Existing agent lanes `/root/auditor`, `/root/tester`, `/root/ui_consumers` have finished. They may be reused on resume; no new agents required.

## Finish after resume

Clarify and reproduce external actual-browser failure, fix with TDD, retest affected gates, verify actual GUI including newselection highlight, update ordinary-English design/analysis/verification/Mermaid to match, independent audit final change, commitcoherently, port final source/docs/evidence, compileandtestboth as necessary. Full feature completion report only after all requirements are genuinelydone. No push/merge or goal creation requested.

## Resumed work

Resumed at 2026-10-04 11:53:08 BST by explicit user request. The earlier pause snapshot above is historical. The user clarified the external check with “how to check external”; no exact failing label/query has yet been observed. A fresh review instance uses /private/tmp/ui-name-resumed-review. Five ordinary-English steps and a result question were provided. A compact actual FileList external-library integration test is being added to cover the saved-file/cache/filter path independently of the existing shared keyword test. No production fix is justified yet.
