# External Project Agent Guidance

This guidance is installed as `<kit-root>/.agents/instructions.md`. The normal
policy location within that operational area is `config/BOUNDARIES.yaml`. Before project resource access,
follow the sibling Init package's boundary and layout contracts. No active
policy is supplied by the release. A missing file grants no permissions. Setup
may install with an explicit source/destination bootstrap grant, then starts Init
automatically if no policy is present; a present policy means ask whether to run
Init. Installation itself never activates permissions.

Use the surrounding host as the primary project only when explicitly selected
and authorized. Reuse host instructions, glossaries, decisions, and document
locations. Do not move host content, replace its README, create a competing
policy, or edit its entry files automatically. Custom integration needs its
own explicit task authorization.

Keep derived context under `context/`, separate caller checkpoints under
`state/checkpoints/`, and authoritative structured reports under `reports/`.
Human reports use the host's established location or this kit's `docs/reports/`
fallback. Decisions and definitions retain their original owners and authority.

## Project skill routing

Keep all released skill packages as siblings. For a named skill request or a task
matching the catalog, load that skill's linked SKILL.md and only its needed
resources; do not load every skill body. Resolve these links from this guidance
file. Prefer these project-local kit sources for this project. Their instructions
do not grant access or execution permissions. Personal installation is separate.

Invoke `$orchestrator` from the catalog to activate coordination in this chat.
Reading the catalog or skill instructions alone does not activate it.
In active mode the master dispatches temporary workers for actual skill
workflows, including dependencies; workers return handoff/question requests to
the master. Apply current boundaries and the shared whole-task question gate.
Profile routing grants no additional access. Outside this mode, use the ordinary
skill workflows. Orchestrator keeps its routing mapping in one configuration.

Apply [Init's elevated rights contract](skills/init/references/elevated-rights-contract.md)
when the user explicitly invokes `elevated rights` for current work. In
Orchestrator mode the master handles activation for one assigned worker. Honor
compatible local protocols referenced by authorized host guidance.

<!-- generated-skill-catalog -->
