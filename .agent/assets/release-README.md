# Agent Skills Workspace

This `Agents/` folder is a self-contained addition to your project. Your existing
README and documentation keep their locations.

Read the [installation and usage guide](../../docs/guide.md). Reusable skill packages
are under `.agent/skills/`; install all released skill folders as siblings. Extraction itself
does not install skills, execute code, or grant project access.

If your project already has an `Agents/` folder, inspect it and agree an update
or another location before extraction. Preserve existing customizations.

Use `$setup` for a first installation when a trusted Setup skill is already available.
After manual extraction, use `$init` to establish the host project and authorized sources.
Setup starts Init automatically only when no boundary policy is present; otherwise
it asks. Policy activation still requires user approval. Project-specific
configuration and agent state are created only when requested. Human project
information stays in its established locations; kit guides and reader-facing
fallback outputs belong under this folder's `docs/` area.
