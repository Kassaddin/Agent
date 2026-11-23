# Installation and Usage

## Install with Setup

If the trusted Setup skill is already available, invoke `$setup` and identify the
local host project. It installs the complete kit from its fixed published-release
repository into a new `Agents/` folder, verifies the release and installed files,
and records the initial baseline for later Update calls. It never replaces an
existing destination, installs personal skill copies, or edits host entry files.

Without boundaries, authorize only the stated source and installation destination.
After verified installation, Setup automatically starts Init when no policy is
present. If a policy is present, it asks whether to run Init. Init still requires
approval of the concrete policy before activation. Installing the kit and
configuring project permissions are separate results.

If Setup is not available yet, use the manual extraction route below and load or
install the reviewed skill packages separately.

## Add the release manually to a project

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

## Shared flow rules

All skills follow the [shared question and assumption rules](../.agent/skills/init/references/boundary-contract.md#questions-and-assumed-answers) and [workflow economy rules](../.agent/skills/init/references/boundary-contract.md#workflow-economy). A user question pauses the whole task. Scoped permission to assume an answer selects its stated recommended option and requires an explicit session-end list of assumed answers and resolutions. These rules preserve existing access and version-control limits.

## Use the skills

| Skill | Intended result |
| --- | --- |
| `$setup` | Verified first installation of the complete project kit, followed by the applicable Init handoff |
| `$init` | Approved, validated project access and engagement boundaries |
| `$glossary` | Consistent terminology with agreement status preserved |
| `$refine` | A minimal yet complete baseline, or resolved assigned choices |
| `$backlog` | Captured, deduplicated, source-linked out-of-scope topics in one project file |
| `$implement` | Direct execution and verification of an agreed small-task Refine baseline |
| `$search` | Located evidence with explicit coverage and limitations |
| `$to-document` | A faithful document after substantive gaps are resolved |
| `$smokes` | An actionable audit report without source corrections |
| `$fix` | Verified corrections from a selected report, when explicitly called |
| `$context` | Relevant source-linked project context, with freshness limits |
| `$update` | Verified published-release updates for this project kit, preserving local edits |

After manual extraction, begin with `$init` in the external project and identify the host project root,
the `Agents/` workspace, and the sources you authorize. Its primary project can
be the surrounding host; that does not authorize every operation there.
The normal kit policy location is `Agents/.agent/config/BOUNDARIES.yaml`.
An existing explicitly selected host policy can be retained instead; never add
a competing policy or select whichever is more permissive. For a custom policy
location, pass the chosen agent area explicitly to helpers that need it.

Existing host instructions are reused. Any integration pointer added to them
requires an explicit, narrowly scoped change. The kit does not overwrite them.

## Retain out-of-scope topics

Invoke `$backlog` or `$refine` to enable capture in the current conversation for
the selected project. Capture may then continue during free-form discussion until
you stop it. It is not enabled across other conversations or by adopting the kit.

Backlog reuses the project's designated file; otherwise it proposes Markdown in
the reader area, normally `docs/backlog.md`. It captures clear deferrals without
asking each time, asks when scope is unclear, and enriches equivalent entries
instead of duplicating them. Entries retain a stable ID, description, exclusion
reason, source, and user/agent origin. No file is needed until there is an item.

Capturing is not approval or a commitment. Required dependencies remain blockers
in the current workflow. This MVP does not prioritize or manage lifecycle. Write
restrictions still apply; unavailable writes return unsaved entries. Backlog does
not require a new specification, decision log, or report for each capture.

## Implement a small task

After agreeing a Refine baseline, request `$implement` to carry it out. The
baseline can remain in the conversation. A small task has bounded scope,
identifiable dependencies, and direct verification against its agreed
requirements; there are no file, line, or duration thresholds.

Implement works across topics within available tools and permissions. It checks
current state, makes the agreed changes, and verifies the result. For a new
substantive choice it prompts the user through a bounded Refine handoff and
pauses the entire task until the answer or an explicitly authorized recommended-answer assumption resolves the question.
Refine completion alone is not implementation authorization.

There is no mandatory document, audit, or correction sequence. Requested document
synthesis uses To Document; a requested audit uses Smokes; acting on its report
uses Fix when explicitly called. Short implementations can finish with a concise
chat result, without another specification or report file.

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

Failed or interrupted updates retain backups and a recovery record. A
pending recovery blocks another update; concurrent edits and missing recovery
permissions are preserved and reported. Readable outcomes link to structured
JSON under the kit's operational reports.

## Recover a first installation

An interrupted Setup installation must be recovered through Setup before Update
can run. Recovery verifies complete installations or removes only identified,
unchanged Setup-created files when permitted. Changed or uncertain content is
preserved. Recovery leaves its records and may leave empty directories; it never
recursively deletes the host or silently reuses an occupied destination.

## Produce a compatible release

Build with an explicit tag such as `--version v1.5.0`, then publish that same tag
with both `agent-skills.zip` and `agent-skills.zip.sha256` as release assets.
Publication is performed by the user. The repository metadata version alone is
not evidence of a published release. Keep historical assets available while
installed kits may need them to verify baselines. The manifest is embedded in
the ZIP and does not hash itself; the sidecar checksum covers the complete ZIP.
