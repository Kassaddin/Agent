# Reusable Agent Skills

Fifteen reusable skills support temporary-worker orchestration, kit installation, project setup, shared terminology, idea refinement, direct implementation, deferred-topic capture, project-local skill authoring,
evidence retrieval, document delivery, task decomposition, auditing, correction, and maintained
project context.

Start with the [installation and usage guide](docs/guide.md). The
[glossary](docs/glossary.md) contains the project's agreed terminology and clearly
separated proposals.

Reader-facing material belongs in `docs/`: guides, terminology, topic decisions,
delivered documents, and readable reports. Local topic records and reports may
be absent from a fresh checkout because they retain their existing private
tracking status.

Agent instructions, reusable skill sources, configuration, context, checkpoints,
and structured reports belong in `.agents/`. The root `AGENTS.md` is only a small
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

Keep all released skill folders under `.agents/skills/` as siblings. Their contracts,
schemas, templates, helpers, and tests travel with them.

To rebuild the package using Python 3.10+:

```text
python -B .agents/scripts/pack_release.py --project-root . --version v2.1.0
```

The build regenerates the 19 bootstrap files and `provenance.json` under
`.agents/skills/setup/bootstrap/` from canonical sources, overwriting local
edits to those generated copies. It writes the complete kit to
`releases/agent-skills.zip` and `releases/agent-skills.zip.sha256` and standalone
Setup to `releases/setup.zip` and `releases/setup.zip.sha256`. Git operations
and publication are separate steps.
