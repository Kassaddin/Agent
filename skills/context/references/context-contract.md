# Context Contract, Version 1

## Ownership and flow

Context owns derived views, the source index, and freshness information. The glossary owns terminology; the designated topic record retains accepted decisions and reasons; artifact owners supply actual update states; the caller maintains the checkpoint and continuation.

Load returns read-only task context to the caller. Build creates an initial view/index only when authorized. Refresh reconciles views affected by canonical-source changes when maintenance is authorized. Context does not rewrite source records, promote proposals, authorize work, or start another delivery workflow.

The caller resolves substantive choices through bounded Refine, lets owners apply and verify changes, and updates its checkpoint. It may then request Context refresh within authorized scope. Search and Smokes write limits remain in force; an audit or retrieval request grants no Context write authority.

## Layout choices

**One context view:** One coherent project orientation with references to the necessary source records.

**Context views by area:** A layout with separate focused area views for complete task-relevant state and selective retrieval.

Start with `CONTEXT.md` plus `context/index.yaml`. Add Markdown under `context/areas/` when necessary orientation exceeds 700 words, several areas have independently changing state, or normal tasks repeatedly need the same focused extraction. These are operational layout criteria, not repository-size classifications. The 700-word budget is a starting orientation target, not a hard content or source-reading limit.

## Index format

Use strict YAML: no duplicate keys, aliases, anchors, tags, or unknown fields. Version 1 has exactly these top-level keys:

| Key | Meaning |
| --- | --- |
| `schema_version` | Integer `1` |
| `project` | Project name matching active boundaries |
| `layout` | `one_view` or `by_area` |
| `root_view` | ID of the global view |
| `views` | Distinct view records |
| `sources` | Canonical source references and review fingerprints |
| `topics` | Topic-to-decision-record/view routing |

Each view has exactly `id`, `path`, and nonempty unique `source_ids`. The root path is `CONTEXT.md`; other views use Markdown paths under `context/areas/`. One-view layout has one view; area layout has at least two including the root. Root sources include glossary and documentation roles.

Each source has `id`, `resource`, `path`, `role`, `owner`, `reviewed_sha256`, and `reviewed_at`; `section` is optional or null. `resource` is a configured boundary source ID. Local paths are portable relative paths within that resource, without parent traversal, absolute paths, or URIs. Paths for views are relative to the primary project. A configured file resource may use `.`. Relative paths never grant access to unlisted or prohibited resolved targets.

Source roles are `glossary`, `decision_record`, and `documentation`. `owner` names the responsible skill. A reviewed fingerprint is a lowercase SHA-256 of the entire file at review; its paired timestamp is ISO 8601 with timezone. Both may be null for unreviewed material. `section`, when present, is a Markdown anchor. A changed file or missing section requires review even if only some content affects a view. Derived Context files cannot be canonical sources, including through a resolved alias.

Each topic has exactly `id`, `decision_source_id`, and nonempty `view_ids`. Its decision source has role `decision_record`. Use the existing scoped record; no additional decision log is created. IDs are unique lowercase names with optional hyphens. References must resolve within the index.

Source membership records view dependencies. Keep source links direct rather than deriving one summary from another. Index review metadata is freshness information; acceptance and authority remain in the owning records.

## Checking and coverage

The read-only checker defaults to the global view. `--view` adds named views; `--source-id` adds sources. `--changed-source-id` selects affected views and their sources, leaving unrelated views unexamined. Unknown IDs are errors, never an invitation to broaden scope.

Defaults: 30 selected sources, 2 MiB per file/index, and a 20-second check budget between operations. Limits may be explicitly adjusted. The checker validates metadata for the index but reads contents only for selected sources/views, with duplicate file reads cached within that call. It never returns source contents or performs network requests.

Source check states are `current` (unchanged since recorded review), `needs_review` (changed, unreviewed, or missing section), `missing`, `blocked`, `unavailable`, `unsupported`, or `not_checked` because of a limit. Local UTF-8 Markdown, YAML, JSON, and text have built-in freshness support. Other formats and usable remotes require authorized adapters; known unusable remotes remain unavailable. Preserve adapter coverage separately when combining results.

Overall `complete` applies only to the declared selected checks with no reported gap; `partial` records incomplete freshness/coverage. A denied index is `blocked`; invalid input is `error`. None establishes factual correctness, agreement, document readiness, or the completeness of the caller's task. Source changes indicate a review need, not automatic falsity.

The caller receives selected views/sources, checked states, affected views, unselected source IDs, topic-record references, and limitations. Context uses actual source review to decide whether an affected view changes and whether a review fingerprint can be updated.
