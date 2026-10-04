# How the names work

Updated 2026-10-04. The diagrams describe current code. The three presentation outcomes are temporary results, not saved enum states. Existing name/library sorting stays unchanged.

| Diagram | Readable image | Mermaid source |
| --- | --- | --- |
| Previous workspace behavior | [image](baseline.svg) | [source](baseline.mmd) |
| One shared display rule | [image](shared-resolution.svg) | [source](shared-resolution.mmd) |
| Three derived presentation outcomes | [image](presentation.svg) | [source](presentation.mmd) |
| DNA through UI | [image](architecture.svg) | [source](architecture.mmd) |
| Permission during name changes | [image](lifecycle.svg) | [source](lifecycle.mmd) |
| Browsing before import | [image](asset-snapshot.svg) | [source](asset-snapshot.mmd) |
| Language switching | [image](runtime-language.svg) | [source](runtime-language.mmd) |
| Group name versus node title | [image](node-renaming.svg) | [source](node-renaming.mmd) |

The lifecycle diagram describes whether an author note exists; it does not introduce a saved state machine. Images are generated from the matching sources. Re-render a changed diagram with the existing Mermaid CLI (`mmdc -i name.mmd -o name.svg -b white`). No runtime Blender dependency is added.

See [implementation](../20261003_231111_implementation-analysis.md) and [verification](../20261003_231111_verification.md).
