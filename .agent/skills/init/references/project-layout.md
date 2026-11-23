# Project Layout Contract

## Audience and adoption

Keep reader-facing definitions, requirements, accepted decisions, delivered documents, and readable reports in the host project's established document locations. Agents use those same canonical sources. Instructions, context indexes/views, execution state, and structured report data belong in a dedicated agent area. File placement grants no permission and creates no additional owner.

This skill repository uses `.agent/` for agent files and `docs/` for readers. A release extracts into a single `Agents/` wrapper: its operational area is `Agents/.agent/`, with kit guidance under `Agents/docs/`. The wrapper never replaces the host README, instructions, configuration, or existing documents. If `Agents/` already exists, inspect it and agree an update or another location before extraction. Keep all released skill folders as siblings, including when installing them into a personal skills directory.

Reuse the host's glossary, topic records, and deliverable locations. Without an established suitable location, propose the kit's `docs/` area for new human artifacts. Create folders only when needed. Do not restructure host content, append host instructions, or overwrite existing files merely to adopt the kit. A minimal existing root `AGENTS.md` may point to dedicated guidance; any host integration change needs its own task authorization.

A conversation-enabled backlog reuses the host's designated reader-facing file.
Without a suitable host destination, Backlog proposes `docs/backlog.md` under the
selected kit/repository root. It is project information, not released guidance or
agent state. One project backlog links its originating topic records; placement
does not enable capture or grant permissions.

## Discovery and paths

An explicitly selected boundary file is authoritative. Otherwise inspect only these known bootstrap candidates within the selected project: `.agent/config/BOUNDARIES.yaml`, `Agents/.agent/config/BOUNDARIES.yaml`, and the legacy root `BOUNDARIES.yaml`. If several exist, require explicit selection; do not choose by permissiveness, validity, or modification time. A missing policy cannot grant access. Follow the boundary contract's bootstrap and validation rules.

The read-only [layout helper](../scripts/project_layout.py) reports these locations:

With no policy file, an unambiguous existing kit area supplies the proposed configuration location; otherwise the repository `.agent/` location is the fallback. Multiple existing areas require explicit selection. Proposing a missing path never creates or activates a policy.

```text
python -B <init-folder>/scripts/project_layout.py --project-root <host-project>
python -B <init-folder>/scripts/project_layout.py --project-root <host-project> --boundaries <selected-file> --agent-home <selected-agent-area>
```

For a policy under `<agent-area>/config/BOUNDARIES.yaml`, the standard agent area ends in `.agent`. A custom location uses explicit `--agent-home`; pass that selection to Context as well. The helper does not validate policy, inspect source contents, write configuration, or establish consent.

Inside the selected agent area, use:

| Purpose | Relative location |
| --- | --- |
| Access policy | `config/BOUNDARIES.yaml` |
| Project-authored skills | `local-skills/<name>/` or an explicitly selected host location outside managed/operational areas |
| Project agent guidance | `instructions.md` |
| Derived context | `context/project.md`, `context/index.yaml`, optional `context/areas/` |
| One checkpoint per topic | `state/checkpoints/<topic>.yaml` |
| Authoritative structured reports | `reports/<workflow>/<run-id>/` |

Human topic records and report destinations are references, not a second project manifest. Reuse existing guidance and Context's source/topic mappings. Pass an explicit human report destination when the host has one; otherwise use the kit's `docs/reports/<workflow>/<run-id>/` fallback.

Project-authored skills normally use `<agent-area>/local-skills/`. Released
kit packages remain in `<agent-area>/skills/`. Local skill content is outside the
release inventory and is not adopted or replaced by Update. Creating those files
does not register them with the host; discovery, host entry edits, personal
installation, and promotion into a published kit are separate requested actions.
Reuse an authorized compatible host location instead of migrating it.

## Checkpoints and reports

Keep accepted choices and reasons in one reader-facing decision record. Keep the caller's one resume checkpoint in the agent area, linked by topic and a decision-record reference containing its configured resource ID and resource-relative path; the Context index records the checkpoint pointer. The [checkpoint schema](../../refine/references/checkpoint.schema.json) defines its shape. Record references and update states, not a second copy of accepted decisions or definitions. Substantive open choices remain visible in the human record. Owners continue supplying actual application and verification status.

Structured audit/fix JSON remains authoritative. Its readable Markdown is derived from that same data and stored with reader-facing reports, linked to the JSON. Delivered reports remain immutable. Moving historical reports does not rewrite their captured old source paths; re-inspect current files before acting on an old finding.

## Compatibility and sharing

Legacy explicit policies outside a dedicated namespace and version-1 context indexes remain readable in their original layout. Do not silently migrate them during Load or Search. New namespaces use context index version 2 and separate checkpoints. Moving configuration does not amend its permissions.

Keep reusable skill sources versioned. Local configuration/state/context/reports and generated releases normally stay ignored; preserve a host's intentional tracking policy. Reader-facing content is not automatically public. Build releases with an explicit allowlist of skill packages and selected kit guidance; never archive the whole operational area or host project.
