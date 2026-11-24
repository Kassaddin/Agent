---
name: update
description: Update a project-local Agents kit from a published release, verifying its baseline and inventory, preserving local edits, and recording verified application or recovery without updating personal skill installations.
---

# Update

Own release selection, verified managed-file replacement, installed-release receipts, and update/recovery outcomes. An explicit update request permits a compatible conflict-free update within existing permissions. A check-only request permits no application. Keep the caller's continuation and separate checkpoint; do not start an unrelated workflow.

## Scope and authority

Read the [boundary contract](../init/references/boundary-contract.md), selected active policy, and [layout contract](../init/references/project-layout.md). Resolve the project-local kit root and configured repository source. First installation belongs to [Setup](../setup/SKILL.md); a pending Setup installation must recover through Setup before updating. Host files outside the selected kit and personal Codex skills directories are never update destinations. A kit may itself be the permitted primary root; this grants no access to its surrounding host. Preserve host layout, project configuration, context, checkpoints, local documents, and unmanaged additions.

Read [the update contract](references/update-contract.md) before using the [helper](scripts/update_kit.py). Its release format is shared with the producer; it does not execute candidate code or issue Git commands. Prefer existing configured read access. Missing source access is a specific blocker for Init, not permission to add sources, change credentials, or weaken policy.

Use the [ownership contract](../refine/references/ownership-contract.md) and [Glossary](../glossary/SKILL.md) for meanings and substantive choices. Use [Search](../search/SKILL.md) when missing release evidence needs discovery; Search returns locators/coverage and never writes Update staging or backups. This helper currently supports configured HTTPS GitHub repositories. Other providers remain unsupported until their adapter is defined.

## Compare before application

Release-update and migration destinations remain inside the kit. Setup's separate,
explicitly approved host-guidance integration may use the shared integration
helper; that operation is not a release update or authority to edit other host files.

For an older `Agents/.agent` kit, use Setup to explain and plan the change first.
Read the [migration contract](references/migration-contract.md). Update owns the
approved migration through [migrate_kit.py](scripts/migrate_kit.py), also bundled
inside standalone Setup. Pin the reviewed plan hash; review any policy relocation.
Verify migration before a separate release-update phase. A pending migration
blocks normal updates; recover through that helper. Existing personal copies or
the development checkout are not migration targets. Structural migration does
not itself establish a completed version update.

Use the latest stable published release unless the user names a version. Do not substitute a branch/tag source archive or silently downgrade. Inspect the published ZIP/checksum, manifest, compatibility, skill identities, and local dependency links without executing scripts from the release.

```text
python -B <update-folder>/scripts/update_kit.py --boundaries <policy> --kit-root <project>/Agents --source <source-id>
```

The helper defaults to a non-writing check. It verifies the installed manifest/receipt against the published baseline. For older kits it checks at most three published packages; an explicit `--baseline-version <tag>` narrows that search. If no baseline is verifiable, stop and explain what remains unknown. Do not infer an unedited installation from file dates, a folder name, or a version label alone.

Local edits, local deletions, and incoming paths already occupied by unmanaged content are conflicts. Preserve them and pause the bundle. A managed file already identical to the candidate needs no replacement. Use an assigned-choice [Refine](../refine/SKILL.md) handoff for unresolved substantive intent, retaining the caller and relevant owner constraints. The helper has no force/automatic-merge option; after an explicitly authorized resolution, compare again.

## Apply and verify

Notify the user of the selected version, changed destinations, additions/removals, and material limits. A separate blanket confirmation is unnecessary for an explicit update call. Ask only for unresolved choices or actual permission gates. Never or user-only rules remain prohibitions. Source or migration changes use Init/Refine as appropriate.

Pin the preview's resolved version and archive hash when applying:

```text
python -B <update-folder>/scripts/update_kit.py --boundaries <policy> --kit-root <project>/Agents --source <source-id> --version <resolved-tag> --apply --expected-sha <preview-sha256> --notified
```

`--notified` records that the caller already gave the required change notification. Supply `--approve operation:project-relative-path` only after actual specific approval for an ask gate; scope it to previewed paths/operations. It never overrides never, source identity, project scope, or personal-installation exclusions. Use `--reader-reports` for an established host report location.

The helper rechecks drift, holds a kit lock, backs up originals, journals its own changes, applies the coherent bundle including new/retired skills, and verifies written bytes before recording the installed release. Keep the current executor stable for the run; do not reload new instructions halfway through. A pending interrupted run blocks another update.

On failure, preserve the backups and attempt bounded recovery of the updater's own changes. Concurrent edits or missing recovery permissions remain explicit blockers. To resume a pending recovery, use the same source/kit/policy with `--recover`, granting only genuinely approved operations. Do not claim rollback completed while recovery is still required.

## Return and record

Return the selected/from versions, changes, verification result, conflict or access blockers, and linked JSON/reader outcome. Outcomes are immutable; a recovery attempt gets another outcome. Supply actual artifact states to the caller's checkpoint. Project Context refresh is optional authorized maintenance, never a second project history.

No published release is a clear no-update result. Identical installed/candidate content is a no-op. Publication remains user-performed. The workflow never fetches, pulls, clones, stages, commits, pushes, updates global installations, or runs candidate install/migration commands.
