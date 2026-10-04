# How to read the verification evidence

The [final verification document](../../20261003_231111_verification.md) is the current result. Implementation, required focused and nearby checks, required visible checks and synchronization are complete. No required blocker remains. The design remains a proposal for Blender core review.

Files in the dated folders are historical snapshots: each records what was known at its own run or observation. They are preserved unchanged, including genuine RED tests, fixture failures, pauses, unsuccessful runs and earlier auditor reservations. A snapshot's open checks do not describe the final state.

| Evidence | Role |
| --- | --- |
| `20261004-original/external-browser-final-*` and `20261004-destination/external-browser-final-*` | Final 77-case focused and nine-check reviewer results |
| `selection-final-*` results in each checkout folder | Retained broader/Python/native/factory results on the same production source; failed and successful reruns are distinct |
| `20261004-original/external-browser-manual.md` | Final user confirmations for external labels/search, personal typing and visible highlight |
| `20261004-destination/external-browser-final-auditor.md` | Final implementation review at the recorded commit |
| `20261004-authorship/` | Commit identity maps and independent identity review |
| `20261004-destination/port.json` | Superseded first-port snapshot; its visible checks were completed afterward |
| Earlier `auditor.md`, `locale-edit-auditor.md`, `selection-final-auditor.md` and `manual-*-observation.md` files | Superseded review/observation snapshots; their earlier reservations remain intact |
| Other earlier logs, XML, JSON, setup notes and summaries | Historical results at their recorded stage, not replacements for the final results |

The [earlier implementation progress](../../20261003_234056_implementation-progress.md) and the historical sections of [RESUME_STATE.md](../../RESUME_STATE.md) are also superseded records. Current commit identity maps explain old hashes without changing original test logs.
