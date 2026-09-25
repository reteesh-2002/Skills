# Antigravity audit evidence bundle

Companion to Antigravity_Architecture_Whitepaper.md and its PDF.

## Reproduce the observed probes

From this directory, run:

    python3 run_probes.py

Requirements: Linux (including /dev/full), Python 3, Node.js with node:test,
Bash and Git. The recorded environment used Node v24.19.0 and Bash 5.2.21.
The script creates tiny isolated fixtures under probes/ and records results.
Several probes intentionally return success for defective behavior. A matched
expected observation is not a product-verification pass.

probe_results.json and probes/*.log are the actual captured observations.
The initial unbounded awaited fixture exceeded a 15-second outer timeout;
the final reproducible fixture adds a 100 ms test timeout.

## Design examples

snippets/ contains the whitepaper's Mermaid diagrams, proposed contracts,
configuration examples and code excerpts. These are reference designs, not
a complete runtime, installed skill package, or certified AGY integration.
JSON blocks were parsed; Bash syntax was checked. The Zod example was not
compiled here. Hook configuration requires a real protected handler and
validation against the installed AGY version.

## Rebuild the PDF

build_whitepaper.py uses pandoc, reportlab and DejaVu fonts. Put the Markdown
at ../output/audit/Antigravity_Architecture_Whitepaper.md relative to this
folder, as in the original task workspace. It draws PDF equivalents of the
Mermaid diagrams; the editable Mermaid source remains in the Markdown.

SHA256SUMS.json records the content hashes of the bundle's files.
