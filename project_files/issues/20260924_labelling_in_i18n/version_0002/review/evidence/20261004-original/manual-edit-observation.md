# User confirmation of selected-language editing

The user first confirmed that Vietnamese stayed visible on entering the editor, then reported that Space immediately replaced the whole label. The real typing-event RED test reproduced that exact selection problem. The generic fix reuses the earlier workspace branch’s no-selection flag.

After the corrected original review instance was reopened, the instruction was: select Vietnamese, double-click the workspace Edit name field, type Space and a suffix, then cancel with Esc. The user replied verbatim: **it works**.

The user’s confirmation verifies the visible typing behavior. Separate direct Blender event assertions cover RNA fields and tabs, real catalog and long supplied translations, Vietnamese characters, Esc and unchanged Enter. No Computer Use capture is claimed. This reply does not confirm the separately requested external-library search check.

The user then stated verbatim: **what to test more? I entered new names in the workspace and saved and reopened it works**. This confirms their workspace personal-name save/reopen check; exact typed names and eligibility UI state were not supplied. The recommended remaining checks were workspace rename-back, undo/redo, and the prepared external-library source/translated queries.

The subsequent normal launch still replaced a saved personal workspace name on Space. The user clarified the name as “Bo tri ... <some test string>” and asked that actual selection be visibly highlighted rather than shown as a black background/end caret. This supersedes the earlier narrow typing approval for personal names. The expanded fix starts every workspace edit unselected and uses the existing text-field highlight when a selection is made. The new visible confirmation is pending; the earlier “it works” is not reused as approval of this new correction.
