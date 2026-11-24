# Project Context Contract, Version 2

## Ownership and flow

Project Context owns derived views, the source index, and freshness information. Glossary owns terminology; the designated reader-facing topic record retains accepted decisions and reasons; artifact owners supply actual update states; the caller maintains its separate checkpoint and continuation. Follow the [project layout contract](../../init/references/project-layout.md) for discovery and non-invasive adoption.

Load returns read-only task context. Build creates an initial view/index only when authorized. Refresh reconciles affected views after canonical-source changes when maintenance is authorized. Project Context never rewrites source records, checkpoints, or permissions, promotes proposals, or starts another delivery workflow.

The caller resolves substantive choices through bounded Refine, lets owners apply and verify changes, and maintains its one checkpoint. It may request authorized affected Project Context Refresh. Search and Smokes write limits remain in force; retrieval/audit requests grant no Project Context write authority.

## Layout choices

**One context view:** One coherent project orientation with references to the necessary source records.

**Context views by area:** A layout with separate focused area views for complete task-relevant state and selective retrieval.

Inside the selected agent area, start with `context/project.md` and `context/index.yaml`. Add Markdown under `context/areas/` when necessary orientation exceeds 700 words, several areas change independently, or repeated tasks need the same focused extraction. The budget is an advisory starting target, never a source-reading or completeness limit. Human project documents stay in established host locations; Project Context references them directly.

## Index format

Use strict YAML: no duplicate keys, aliases, anchors, tags, or unknown fields. Version 2 has exactly these top-level keys:

| Key | Meaning |
| --- | --- |
| `schema_version` | Integer `2` |
| `project` | Name matching active boundaries |
| `layout` | `one_view` or `by_area` |
| `root_view` | Global view ID |
| `views` | Distinct view records |
| `sources` | Canonical source references and review fingerprints |
| `topics` | Decision-record, separate-checkpoint, and view routing |

Each view has exactly `id`, `path`, and nonempty unique `source_ids`. Paths are relative to the primary project: the root view is `<agent-area>/context/project.md`; area views are under `<agent-area>/context/areas/`. One-view layout has one view; area layout has at least two including the root. Root sources include glossary and documentation roles.

Each source has `id`, `resource`, `path`, `role`, `owner`, `reviewed_sha256`, and `reviewed_at`; `section` is optional or null. Resource is a configured boundary source ID; paths are portable resource-relative paths without absolute paths, parent traversal, or URIs. A configured file resource may use `.`. Source roles are `glossary`, `decision_record`, and `documentation`; owner names the responsible skill.

The paired review fields are a lowercase whole-file SHA-256 and ISO 8601 timestamp with timezone, or both null for unreviewed material. An optional section is a Markdown anchor. Changed content or a missing section needs review. Derived Project Context files cannot be canonical sources, including through resolved aliases. Path references never grant additional access.

Each topic has exactly `id`, `decision_source_id`, `checkpoint_path`, and nonempty `view_ids`. Its source has role `decision_record`; the project-relative checkpoint path is unique to that topic and inside `<agent-area>/state/checkpoints/`. The [checkpoint schema](../../refine/references/checkpoint.schema.json) requires the same topic and decision-record resource/path reference. Applied/verified updates need evidence; the caller owns their truth and maintenance. Project Context checks linkage and structure, never infers completion from them.

IDs are unique lowercase names with optional hyphens. All references resolve within the index. Keep sources direct instead of deriving one summary from another. Do not copy decisions, definitions, or checkpoint contents into another independently editable log.

## Checking and coverage

The checker defaults to the global view. `--view` adds views; `--source-id` adds sources. `--changed-source-id` selects affected views and necessary sources. Unknown IDs are errors and never broaden scope. `--agent-home` selects a custom in-project operational area when it cannot be inferred from the selected boundary path.

Defaults are 30 selected source/checkpoint checks, 2 MiB per file/index, and a 20-second budget between operations. The index metadata is validated globally, but only selected sources/views and their topic checkpoints are read. Duplicate reads are cached. The helper never writes files, executes inspected content, or performs network requests.

Source states are `current` (unchanged captured bytes since recorded review), `needs_review`, `missing`, `blocked`, `unavailable`, `unsupported`, or `not_checked` due to limits. Built-in freshness support covers local UTF-8 Markdown, YAML, JSON, and text. Remote/binary evidence requires authorized adapters with explicit coverage. Unsupported evidence never becomes a negative finding automatically.

Overall `complete` applies only to the selected checks with no reported gap; `partial` records limits. Denied indexes are `blocked`; invalid inputs are `error`. None proves agreement, factual correctness, document readiness, or task completion. Changed sources indicate review needs, not automatic falsity. Source review, not a hash update alone, determines Refresh.

## Legacy compatibility

An explicitly selected legacy policy outside the dedicated namespace retains the version-1 root layout: `CONTEXT.md`, `context/index.yaml`, and `context/areas/`. Version-1 topics have no checkpoint-path field. Read them without automatic migration or copying embedded checkpoints. New namespaces use version 2. A requested migration separates checkpoints and updates references explicitly; it never changes policy permissions or rewrites historical report evidence.
