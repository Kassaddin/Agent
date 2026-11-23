# External Project Agent Guidance

This guidance is installed as `<kit-root>/.agent/instructions.md`. The normal
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

Keep all released skill packages as siblings when installing them. Package files
are references and tools, not permission to execute arbitrary project code.
