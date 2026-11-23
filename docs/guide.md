# Installation and Usage

## Add the release to a project

The release archive contains one top-level `Agents/` folder. Inspect the archive
before extraction. If the host already contains `Agents/`, review its ownership
and contents before agreeing an update or a different destination; do not merge
over it blindly.

For a new destination, extract alongside the host's existing README and project
folders. The kit's guide is `Agents/README.md`, its reader documentation is under
`Agents/docs/`, and its operational area is `Agents/.agent/`. Extraction adds no
root README, active access policy, project context, or host instruction file.

The kit's own `.gitignore` applies only inside `Agents/`, keeping its local
configuration, state, and reports out of normal version-control additions.
The host's ignore file and intentional tracking policy remain under its control.

The kit keeps its own material together. Project glossaries, decisions,
requirements, and delivered documents use the host's established locations.
Only new content without a suitable host destination uses the kit's reader area.
Folder placement grants no access to the surrounding project.

## Make the skills available

The complete released packages are under `Agents/.agent/skills/`. Copy their
folders as siblings into your personal Codex skills directory, normally
`~/.codex/skills` (`%USERPROFILE%\.codex\skills` on Windows), or the `skills`
directory of your configured Codex home. Review existing customizations before
replacing installed copies. Installed skills become available on your next turn.

Repository development uses the same packages under `.agent/skills/`; personal
installation does not move the project's documents or operational area.

Python 3.10+ and PyYAML 6.x are needed for the validation/search helpers. The
dependency declaration is the Init package's `scripts/requirements.txt`. Regex
search additionally needs ripgrep (`rg`). Install dependencies only when you
choose to do so; extraction does not install or run anything.

## Use the skills

| Skill | Intended result |
| --- | --- |
| `$init` | Approved, validated project access and engagement boundaries |
| `$glossary` | Consistent terminology with agreement status preserved |
| `$refine` | A minimal yet complete baseline, or resolved assigned choices |
| `$search` | Located evidence with explicit coverage and limitations |
| `$to-document` | A faithful document after substantive gaps are resolved |
| `$smokes` | An actionable audit report without source corrections |
| `$fix` | Verified corrections from a selected report, when explicitly called |
| `$context` | Relevant source-linked project context, with freshness limits |
| `$update` | Verified published-release updates for this project kit, preserving local edits |

Begin with `$init` in the external project and identify the host project root,
the `Agents/` workspace, and the sources you authorize. Its primary project can
be the surrounding host; that does not authorize every operation there.
The normal kit policy location is `Agents/.agent/config/BOUNDARIES.yaml`.
An existing explicitly selected host policy can be retained instead; never add
a competing policy or select whichever is more permissive. For a custom policy
location, pass the chosen agent area explicitly to helpers that need it.

Existing host instructions are reused. Any integration pointer added to them
requires an explicit, narrowly scoped change. The kit does not overwrite them.

## Read results and resume work

Read accepted decisions and reasons in the designated human topic record.
The caller's separate checkpoint holds operational continuation and references
that record. There is one of each, not a new record for every skill.

Readable audit/fix reports use the host's report location or the kit's
`docs/reports/` fallback. They link to authoritative JSON under the agent area.
Reports remain historical snapshots; a later correction rechecks current files.

Context is a derived view for agents. It does not replace canonical documents,
promote proposed terms, grant permissions, or establish document readiness.


## Update a project kit

Invoke `$update` with the project kit and its approved repository source. It
selects the latest stable published release unless you name a published version.
The first helper call compares without writing; an explicit update request then
permits a compatible, conflict-free installation within current permissions.
You receive a change notification. Actual permission gates and local conflicts
still require a decision; there is no automatic merge or force overwrite.

Update changes only the kit's managed files, including released skills and kit
guidance. It preserves host documents, project permissions/configuration,
context/checkpoints, local reports, and unmanaged additions. Personal Codex
skill copies remain unchanged by this workflow. To use updated functionality,
load the project-local skill files; a separate personal installation update is
outside this skill's scope.

New releases contain `.agent/release/manifest.json` inside the kit, identifying
the release and file hashes. Update records the verified installed identity in
its own local state. An older kit needs a verifiable matching published baseline;
otherwise it stops. A known `--baseline-version` can identify that package.
It never substitutes an arbitrary branch source archive for a published package.

Failed or interrupted installation retains backups and a recovery record. A
pending recovery blocks another update; concurrent edits and missing recovery
permissions are preserved and reported. Readable outcomes link to structured
JSON under the kit's operational reports.

## Produce a compatible release

Build with an explicit tag such as `--version v1.1.0`, then publish that same tag
with both `agent-skills.zip` and `agent-skills.zip.sha256` as release assets.
Publication is performed by the user. The repository metadata version alone is
not evidence of a published release. Keep historical assets available while
installed kits may need them to verify baselines. The manifest is embedded in
the ZIP and does not hash itself; the sidecar checksum covers the complete ZIP.
