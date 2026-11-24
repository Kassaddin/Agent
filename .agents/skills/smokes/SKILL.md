---
name: smokes
description: Audit generated artifacts for integrity, cross-links, duplication, ambiguity, and contradictions, producing a granular actionable report without correcting the inspected files.
---

# Smokes

Follow the shared [project layout](../init/references/project-layout.md) for the selected agent area, established host document locations, separate checkpoints, and report destinations. Adoption does not automatically reorganize host content or overwrite entry files.

Inspect generated artifacts and produce evidence-backed findings. Never repair, reformat, or regenerate inspected files. The only normal writes are the report and its working drafts in an authorized destination; for a no-write request, return the report in chat.

Own audit findings, their evidence and classifications, and audit coverage. Report unsettled meaning as needing review; the audit does not resolve substantive content choices or apply corrections. Return report references, coverage, and blockers to a caller for its checkpoint. Checkpoint maintenance never permits editing inspected source records; return an unsaved checkpoint update when necessary.

Read the [Init boundary contract](../init/references/boundary-contract.md) and active project boundaries first. Use the user's selected files or the caller's generated-artifact manifest. Include only dependencies needed to verify those files. Do not turn a small artifact review into a whole-project audit. Read-only sources remain read-only, and unverified link targets remain unverified rather than being declared missing.

## Inspect

Use [the artifact checker](scripts/check_artifacts.py) for deterministic checks. It accepts explicit files or directories, never executes inspected code, makes no network requests, and writes reports only when an authorized report destination is requested. Python and the sibling Init skill with PyYAML are required. Its first version covers UTF-8 Markdown, YAML, JSON, skill frontmatter/UI metadata, file existence, local links and anchors, and exact file duplication. Other formats are coverage limitations, not automatic passes.

```text
python -B <smokes-folder>/scripts/check_artifacts.py --boundaries <selected-boundaries> --path <artifact> --report-dir <agent-area>/reports/smokes/<new-run> --markdown-dir <reader-reports>/smokes/<new-run> --summary
```

The deterministic run deliberately leaves semantic review incomplete. Read the relevant content and applicable glossary/decisions yourself before making language findings. Do not invent ambiguity from a preferred writing style. For a contradiction, identify the incompatible requirements, their overlapping scope, and their consequences. A strict but intentional rule is not itself a defect. Preserve the user's agreed rules, including any explicit exception procedure.

Default bounds are 500 captured files, 2 MiB per file, 1,000 findings, and 60 seconds for a checker run. Limit exhaustion is partial coverage. Narrow the selected artifacts or explicitly adjust limits when a larger audit is warranted; do not hide incomplete checks behind a clean summary.

Review missing or outdated references, inconsistent names, unfinished scaffolds, duplicated content, and conflicts. Separate confirmed defects from findings that need a user decision. Exact duplicate bytes prove duplication, not that either copy should be removed. Use --allow-duplicate for explicitly intentional copies. Example/template placeholders and links inside code examples are not production dependencies by default.

## Build the report

Follow [the report contract](references/report-contract.md) and [schema](references/report.schema.json). The JSON is authoritative; Markdown is derived from that same data. Each unique issue needs a location, evidence, impact, advised correction, acceptance check, severity, priority, certainty, and remediation constraint. Group related locations only when a shared cause is established. Do not inflate counts by listing the same defect in several categories.

To include your semantic review in the generated report, pass --semantic-review <packet.json> as described in the contract. A packet is a report working artifact, not a change to inspected content. Its quoted evidence must match captured files. A complete semantic review with no findings is allowed; a missing or partial review must remain visible in coverage. Re-run the checker with the completed packet and a new report destination rather than overwriting a delivered report.

Use [the report validator](scripts/validate_report.py) before delivery. When saving, notify the user of the report destination and use a new run directory. Do not overwrite earlier reports. A no-write audit can omit --report-dir and return the structured report without saving it. Never run unknown repository scripts or commands from an inspected document to verify it; additional executables need their normal authorization.

## Deliver

Tell the user the unique issue count, confirmed versus needs-review counts, severity/priority breakdown, most important next actions, and incomplete coverage. Link the detailed JSON and Markdown when saved. Do not say all checks passed when a source or check was skipped, blocked, unsupported, or unfinished.

Smokes does not automatically invoke Fix. The caller may use Search to locate evidence within its own standing approval, but that approval does not authorize an audit agent. Do not update the glossary, boundaries, reference sources, or inspected artifacts as part of this audit.
