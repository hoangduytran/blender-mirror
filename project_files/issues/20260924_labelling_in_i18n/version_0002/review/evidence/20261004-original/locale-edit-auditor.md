# Independent translated-name editing audit

No source blocker found in the final draft.

The existing no-selection flag is enabled only for an edit with a distinct translated snapshot, then restored to its prior state. Dynamic-buffer mode is reset at every edit start and enabled for translated snapshots; the existing insertion path updates both the owned buffer and button edit pointer after reallocation. Ordinary edits retain existing selection and buffer behavior. Cancel and unchanged confirmation preserve raw names and author notes; deliberate changes use the ordinary setter and clear the note. Outliner note-only edits retain undo and notifications.

No DNA field or persisted display-state enum was added. RNA/bpy names remain raw. Snapshot allocation happens at edit start, not ordinary label drawing.

The actual event test imports bpy inside its generator, preserving host-side discovery. It checks Space before selecting text, then appends UTF-8, checks Escape and unchanged Enter, for ordinary RNA fields and workspace tabs, including a registered translation longer than 255 bytes. This tests real handlers rather than helper-only behavior. The recorded RED log contains the actual assertion `space != Bố Trí plus space`, reproducing the user report. The GREEN log is empty, so successful exit status must be established by the executor record rather than inferred from that file alone.

Reviewed implementation-analysis code excerpts match the inspected begin/apply helpers and selection setup. Its pending verification wording remains appropriate until measured results are recorded. No claim of manual GUI confirmation is supplied by this audit.

## Committed original verification update

Inspected commits 3bfa127c7de, beb4c53bced and 8d4ce0b999e. Original direct-child typing summary records exit 0, and foreground undo records exit 0 with three passing checks. Focused XML records 75 tests; broader XML records 37 and BLI XML 3, with zero failures, errors or disabled tests. The nine-check reviewer summary passes. Exact editor code excerpts match source; Mermaid SVG labels reflect the updated edit lifecycle. Current destination repetition is explicitly pending. Manual visible first-keystroke/external FileList/multiple-window evidence remains separately identified. One minor stale wording in verification line 47 says current evidence is pending even though the evidence commit exists; final port is the pending item. No new source blocker found.
