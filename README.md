# Reusable Agent Skills

Twelve reusable skills support kit installation, project setup, shared terminology, idea refinement, direct implementation, deferred-topic capture,
evidence retrieval, document delivery, auditing, correction, and maintained
project context.

Start with the [installation and usage guide](docs/guide.md). The
[glossary](docs/glossary.md) contains the project's agreed terminology and clearly
separated proposals.

Reader-facing material belongs in `docs/`: guides, terminology, topic decisions,
delivered documents, and readable reports. Local topic records and reports may
be absent from a fresh checkout because they retain their existing private
tracking status.

Agent instructions, reusable skill sources, configuration, context, checkpoints,
and structured reports belong in `.agent/`. The root `AGENTS.md` is only a small
bootstrap pointer. Repository metadata remains at the root.

## Releases

The generated package is `releases/agent-skills.zip`, accompanied by its SHA-256
file. Each build requires an explicit SemVer release tag and embeds a managed-file manifest. It contains one top-level `Agents/` folder, reusable skills, and selected
kit guidance. It excludes this repository's access policy, project glossary,
decisions, checkpoints, context, and reports.

Adding the release to another project does not replace that project's README,
instructions, configuration, or document layout. Existing project information
remains authoritative in its established locations.

## Develop and package

Keep all released skill folders under `.agent/skills/` as siblings. Their contracts,
schemas, templates, helpers, and tests travel with them.

To rebuild the package using Python 3.10+:

```text
python -B .agent/scripts/pack_release.py --project-root . --version v1.5.0
```

This command writes only the generated ZIP and checksum under `releases/`.
It does not modify Git history, stage changes, or publish anything.
