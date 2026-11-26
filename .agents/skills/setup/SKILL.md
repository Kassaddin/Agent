---
name: setup
description: Bootstrap the complete project kit from published releases using only this self-contained package, plan legacy migrations for Update, and arrange approved project guidance integration.
---

# Setup

Own first installation, legacy-layout detection and migration planning, and the
installation continuation. This complete `setup/` folder is self-contained; no
sibling skills need to be installed first. Its generated `bootstrap/` resources
come from canonical Init, Smokes, and Update sources; do not maintain those copies
independently. Python 3.10+ and PyYAML 6.x remain environment prerequisites.

Read the bundled [boundary contract](bootstrap/init/references/boundary-contract.md),
[layout contract](bootstrap/init/references/project-layout.md), and
[Setup contract](references/setup-contract.md). Follow the shared question rules
and current active policy. Missing boundaries grant no permission. Do not start
a policy interview merely to inspect a bootstrap request.

## Establish source, destination, and authority

Use only published releases from `https://github.com/Kassaddin/Agents`. Identify
the existing host project. The exact kit destination is its direct `Agents/`
child with `.agents/` as its operational area. Enforce kit-owned structure there;
reuse host documents and preserve unrelated project content and local additions.
Retain existing local elevated rights protocol files and their guidance pointers
under the [bundled Init contract](bootstrap/init/references/elevated-rights-contract.md#existing-project-protocols).

Use the [trusted helper](scripts/setup_kit.py), which imports only resources
inside this package. Existing boundaries must be valid, active, and authorize
the affected source/paths. Multiple old/new policy candidates require explicit
selection. With no policy, obtain actual scoped source-and-destination bootstrap
authorization. Flags record existing approval; they never establish consent.
Never/user-only rules and platform gates still apply.

## Preview, then take the applicable path

The helper defaults to a non-writing check. Select the latest stable published
release unless the user names a published tag; pin the resolved tag/hash for apply.
Require layout 3/protocol 2, complete inventory, checksum, manifest, syntax,
and local dependency links. Stop on incompatible assets or inaccessible evidence;
never substitute a branch archive or execute candidate code.

```text
python -B <setup>/scripts/setup_kit.py --project-root <host> --boundaries <policy> --source <release-source-id>
```

Without a policy use `--bootstrap-approved` only after the exact bootstrap grant.
For a fresh destination, notify the user of concrete changes; apply with
`--version <tag> --apply --expected-sha <preview-sha> --notified` under current
permissions. Exclusively create the kit, journal writes, verify bytes, and record
the initial release receipt. Interrupted first installation recovers through
this helper with `--recover`; preserve concurrent edits and uncertain data.

If `Agents/.agent/` exists, explain the change and return the Update-owned
[migration plan](bootstrap/update/references/migration-contract.md), including
file mappings, conflicts, and any concrete policy preview. Obtain approval before
execution. **Setup does not execute migration or automatically update the kit.**
Hand the reviewed plan/hash to the bundled Update-owned helper:

```text
python -B <setup>/bootstrap/update/scripts/migrate_kit.py --project-root <host> --boundaries <policy> --source <release-source-id>
```

The Update phase uses `--apply --migration-approved --expected-plan-sha <hash>`
only after real approval; affected policy relocation also requires
`--policy-reviewed`. Its `--recover` resumes recorded migration. Verify migration
first, then run a separate requested release-update preview/application through
the bundled Update helper. Do not depend on the old installed updater understanding
the new layout. Unknown baselines and local managed edits remain blockers.
If the migrated kit has no active policy, load its installed Init skill before
release updating or host integration; the bootstrap grant is not lasting policy.
An occupied canonical destination routes to an explicit Update request; arbitrary
occupied folders are conflicts, never silently adopted or overwritten.

## Continue to Init and approved project integration

After verified fresh installation, load the installed
`<host>/Agents/.agents/skills/init/SKILL.md`. Start Init automatically only when
no policy exists; otherwise ask whether to run it. Init retains the interview,
concrete approval, and activation. Reuse known project/source facts without
inventing answers. Installation, activation, and integration are separate states.
Pass the known `Agents/.agents` agent area and proposed configuration path to Init
when no policy exists; do not ask it to infer a competing host location.

Use the bundled [integration helper](bootstrap/update/scripts/integrate_project.py)
to preview a minimal host `AGENTS.md` pointer to the installed kit guidance after
Init. Check the concrete preview against any explicitly referenced local protocol
and its pointers as directed by the bundled Init contract. Show the addition
and each legacy kit-pointer rewrite. Obtain approval, then apply with the
preview hash. Preserve unrelated bytes and retain a backup. If current
policy does not cover the host entry file, ask for the exact access action.

The kit guidance supplies a generated skill catalog and loads only relevant
project skill instructions. Verify that its references resolve without personal
skill copies. Registration in a global skill menu/personal directory remains a
separate operation. Report pending integration honestly if declined or blocked.

## Deliver

Report version, location, verified installation or migration-plan status,
Init and integration states, and outcome references separately. Keep the caller's
continuation. Migration execution and subsequent updates belong to Update;
permissions belong to Init. Do not install dependencies, publish releases, or
perform version-control mutations.
