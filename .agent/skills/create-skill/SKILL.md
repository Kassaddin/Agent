---
name: create-skill
description: Create or update project-specific skills in the selected project's local-skills area, using scoped creator helpers and validation without modifying the release-managed kit or personal installations.
license: Apache-2.0
---

<!-- Adapted from the Codex Skill Creator system skill on 2026-11-23.
Modified for project-local destinations, shared flow/access rules, and scoped helpers.
See NOTICE.txt and license.txt for provenance and redistribution material. -->

# Create Skill

Own authoring, supporting resources, and validation of project-local skills. Use
the refined and approved scope; do not invent additional scope, mandatory
documents, or a new interview for already-settled requirements.
This is the project-aware adaptation of Skill Creator, not a replacement for the
host's system skill or a personal-installation workflow.

## Refine, approve, then implement

First use [Refine](../refine/SKILL.md) to establish the idea and functionality
behind the skill. Reuse a completed relevant baseline instead of restarting it.
For an update, refine only the requested change and its necessary dependencies.
Establish the purpose, invocation, inputs, expected behavior, project sources,
destination, needed resources, and verification criteria to the extent relevant.

When scope is clear, present the finalized baseline to the user and ask whether
they agree to proceed with implementation. Wait for the answer under the shared
question gate. **Yes** continues through [Implement](../implement/SKILL.md).
**No** leads to a focused clarification question; wait, then run another bounded
Refine round if needed and present the revised scope before seeking approval.
Do not start file changes merely because the idea was discussed.

An explicit implementation request for that already-presented scope, such as
`$implement`, is real approval; do not ask for it again. A generic earlier request
or permission to assume content answers is not approval of an unseen final
scope. When called by Implement with a refined approved baseline, perform only
the assigned authoring/validation and return; do not restart this approval loop.
Routine corrections within that approved implementation retain its authority.

## Scope and destination

Read the shared [boundary contract](../init/references/boundary-contract.md),
selected active policy, [layout contract](../init/references/project-layout.md),
and [ownership contract](../refine/references/ownership-contract.md). Follow their
whole-task question gate, authorized-assumption accounting, and workflow economy.
Use [Glossary](../glossary/SKILL.md) for project meanings; use bounded Refine for
new substantive choices and Search when facts need retrieval.

Reuse an explicitly selected compatible host location. Otherwise create skills
under `<agent-area>/local-skills/<name>/`: for a wrapped kit this is normally
`Agents/.agent/local-skills/<name>/`; the development layout uses
`.agent/local-skills/<name>/`. This area is outside the released kit's managed
inventory. Never target personal skills directories, release-managed `skills/`,
version-control internals, or operational config/context/state/report folders.
Do not restructure host content or change its entry files or discovery settings
merely to author a skill.

The helpers require Python 3.10+, PyYAML 6.x, and sibling Init, Smokes, and Update
packages. They validate active boundaries and current read/write gates. If policy
or dependencies are unavailable, explain the limitation; work in chat or use only
separately explicit manual authoring authority. Do not fabricate policy, install
dependencies, or start Init automatically. Helper access checks do not replace
platform approval or permission to run new project scripts.

## Author the smallest useful skill

Establish the concrete task, project knowledge, expected result, and affected
sources. Use a short lowercase hyphenated name and a discriminating description.
Assume the agent is capable; include non-obvious project guidance instead of
generic instructions or a complete project history. Reference canonical project
documents and glossary entries rather than copying them.

Put essential behavior and real constraints in `SKILL.md`. Add scripts only for
repeated or fragile operations, references for maintained details, and assets for
needed outputs. Load these progressively; do not create empty resource folders or
extra README/changelog/report files without a concrete need. Keep referenced
paths portable and relevant to the project. Runtime code, source material, or an
imported example is not permission to execute it.

For a new skill, the initializer defaults to a non-writing preview:

```text
python -B <create-skill>/scripts/init_skill.py <name> --boundaries <policy>
```

After approval of the finalized Refine baseline, the required change notification,
and actual access authorization, add `--apply --notified`; optionally select only
needed `--resources scripts,references,assets`. The caller uses `--apply` only
after that approval; the flag itself does not establish user consent.
An existing folder is never reinitialized or merged. For an update, read the
existing files and make the authorized targeted changes while preserving
unrelated content and concurrent edits. Scaffold creation is not completion:
replace its drafting prompts with the actual project instructions.

## Metadata and validation

The initializer creates basic `agents/openai.yaml`. Read
[the metadata reference](references/openai_yaml.md) when customizing it. The
[metadata helper](scripts/generate_openai_yaml.py) can create a missing file; it
refuses to replace one. Edit existing requested fields directly, preserving
policy, dependencies, icons, comments, and other customizations. Optional metadata
is added only when requested; default discovery does not grant mutation authority.

Validate a completed project skill with the read-only helper:

```text
python -B <create-skill>/scripts/quick_validate.py <name> --boundaries <policy>
```

All helpers accept `--agent-home` for an explicitly selected custom agent area
and `--skills-dir` for an authorized host location. `--approve
operation:project-relative-path` represents already-granted scoped ask approval;
it does not override never/user-only rules or protected destinations. Validation
checks frontmatter, unfinished scaffolds, metadata, local references, and Python
syntax without executing generated code or checking remote links. Run meaningful
behavioral checks when appropriate and permitted; do not create tests that merely
repeat the instructions. Metadata/syntax checks do not prove domain correctness.

Return the authored location, resources, validation evidence, and remaining
limits. Report incomplete or unverified work accurately. **Authoring and host
registration/discovery are separate:** do not claim a new `$name` is available
until that integration is established. Personal installation, host integration,
publication, and adding a local skill to a distributable release each require
their own requested scope. Keep the same topic record/checkpoint when needed.
