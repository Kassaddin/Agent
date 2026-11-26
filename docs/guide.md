# Installation and Usage

## Install with standalone Setup

Obtain the complete `setup/` folder from `setup.zip` and verify its accompanying
checksum. Make that one skill available to your agent, then invoke Setup for the
current host project. Python 3.10+ and PyYAML 6.x are required. No sibling skills
need to be installed first; bootstrap helpers are bundled from maintained sources.

Setup previews and verifies a complete kit from its fixed
[release source](../.agents/skills/setup/references/setup-contract.md), then installs
it into the host's `Agents/` folder using `.agents/` for agent material. It preserves the
surrounding project structure. Installation writes the initial verified receipt.
Init runs automatically only when no policy exists; otherwise Setup asks whether
to run it. Init still needs concrete policy approval before activation.

For an existing old `.agent` kit, Setup explains the new layout and plans the
migration first. Update applies the approved migration and verifies it before a
separate requested release update. Local edits, occupied targets, unknown
baselines, and policy changes are exposed before application. Interrupted work
retains a bounded recovery journal; uncertain concurrent changes are preserved.

After Init, Setup previews minimal project AGENTS.md guidance integration. Approve
the exact addition and any old kit-link rewrites before applying. Existing content
is preserved and backed up. The linked kit guidance supplies a generated skill
catalog and loads relevant project instructions without installing every package
globally. Installation, migration, policy activation, integration, and updating
are reported as distinct states. Personal installation remains optional/separate.

## Add the release manually to a project

The release archive contains one top-level `Agents/` folder. Inspect the archive
before extraction. If the host already contains `Agents/`, review its ownership
and contents before agreeing an update or a different destination; do not merge
over it blindly.

For a new destination, extract alongside the host's existing README and project
folders. The kit's guide is `Agents/README.md`, its reader documentation is under
`Agents/docs/`, and its operational area is `Agents/.agents/`. Extraction adds no
root README, active access policy, project context, or host instruction file.

The kit's own `.gitignore` applies only inside `Agents/`, keeping its local
configuration, state, and reports out of normal version-control additions.
The host's ignore file and intentional tracking policy remain under its control.

The kit keeps its own material together. Project glossaries, decisions,
requirements, and delivered documents use the host's established locations.
Only new content without a suitable host destination uses the kit's reader area.
Folder placement grants no access to the surrounding project.

## Optional personal skill installation

The complete released packages are under `Agents/.agents/skills/`. Copy their
folders as siblings into your personal Codex skills directory, normally
`~/.codex/skills` (`%USERPROFILE%\.codex\skills` on Windows), or the `skills`
directory of your configured Codex home. You can compare the installed copies with
the release manifest to check their currency. Review existing customizations before
replacing them. Installed skills become available on your next turn.

Repository development uses the same packages under `.agents/skills/`; personal
installation does not move the project's documents or operational area.

Python 3.10+ and PyYAML 6.x are needed for the validation/search helpers. The
dependency declaration is the Init package's `scripts/requirements.txt`. Regex
search additionally needs ripgrep (`rg`). Install dependencies only when you
choose to do so; extraction does not install or run anything.

## Shared flow rules

All skills follow the [shared question and assumption rules](../.agents/skills/init/references/boundary-contract.md#questions-and-assumed-answers) and [workflow economy rules](../.agents/skills/init/references/boundary-contract.md#workflow-economy). An interactive user question pauses the whole task. In separately requested unattended work, stop safely and report a required unresolved question or blocker. Scoped permission to assume an answer selects its stated recommended option and requires an explicit session-end list of assumed answers and resolutions. These rules preserve existing access and version-control limits.

## Use the skills

| Skill | Intended result |
| --- | --- |
| `$orchestrator` | Coordination of temporary skill workers, acceptance, and consolidated delivery in this chat |
| `$elevated-rights` | Explicit temporary consent for scoped local work |
| `$setup` | Verified first installation of the complete project kit, followed by the applicable Init handoff |
| `$init` | Approved, validated project access and engagement boundaries |
| `$glossary` | Consistent terminology with agreement status preserved |
| `$refine` | A minimal yet complete baseline, or resolved assigned choices |
| `$backlog` | Captured, deduplicated, source-linked out-of-scope topics in one project file |
| `$implement` | Direct execution and verification of an agreed small-task Refine baseline |
| `$create-skill` | Refined, approved, authored, and validated project-specific skills outside the managed kit |
| `$search` | Located evidence with explicit coverage and limitations |
| `$to-document` | A faithful document after substantive gaps are resolved |
| `$to-tasks` | Bounded tasks traced to a documented scope and its agreed parent baseline |
| `$smokes` | An actionable audit report without source corrections |
| `$fix` | Verified corrections from a selected report, when explicitly called |
| `$project-context` | Relevant source-linked project context, with freshness limits |
| `$update` | Verified published-release updates for this project kit, preserving local edits |

After manual extraction, begin with `$init` in the external project and identify the host project root,
the `Agents/` workspace, and the sources you authorize. Its primary project can
be the surrounding host; that does not authorize every operation there.
The normal kit policy location is `Agents/.agents/config/BOUNDARIES.yaml`.
An existing explicitly selected host policy can be retained instead; never add
a competing policy or select whichever is more permissive. For a custom policy
location, pass the chosen agent area explicitly to helpers that need it.

Existing host instructions are reused. Any integration pointer added to them
requires an explicit, narrowly scoped change. The kit does not overwrite them.

## Coordinate work in one chat

Invoke `$orchestrator` to make the current chat the master for subsequent work
until you stop the mode. The master handles clarification, dispatch, acceptance,
and final delivery; temporary workers perform the actual skill workflows. Each
invocation, including a dependency, receives a worker. Other chats are unaffected.
The host must support temporary sub-agents and the selected settings; unavailable
capabilities are reported instead of silently replaced with persistent chats.

The single [routing configuration](../.agents/skills/orchestrator/references/profiles.yaml)
maps each production skill to a default profile with ordered GPT, Claude, and
Gemini candidates. Orchestrator selects the least-intensive suitable approved
profile and the first candidate whose model and effort the host supports. A
fallback within a profile does not use the assignment's one automatic escalation.
Demanding effort escalation uses the current worker's model. Urgency changes
priority without lowering acceptance. Routing grants no resource or action permissions.

Workers send questions and permission requests to the master. The master
applies the shared question rules across the task. It also handles the user's
elevated rights command as a control operation for one identified worker.

Workers return verified results and context deltas. The master accepts them and
coordinates authorized Project Context reconciliation, keeping existing decisions
and one caller checkpoint rather than per-worker histories. Unavailable context
maintenance is reported pending. Finished workers become inactive; the host may
retain internal history. No persistent service or personal installation is added.

## Grant temporary elevated rights

Use an explicit `elevated rights` command in the task request or during work.
In ordinary chat this applies to the agent performing the current task. In
Orchestrator mode it applies to one identified worker's assignment. The agent
states the scoped resources and effects before using the grant for eligible
local `ask` decisions. Follow the [Init contract](../.agents/skills/init/references/elevated-rights-contract.md)
for expiration, protected effects, and compatibility with host protocols.

## Retain out-of-scope topics

Invoke `$backlog` or start direct or whole-topic `$refine` to enable capture for
the selected project in the current conversation. A bounded assigned-choice Refine
handoff can use already active capture. Capture may continue during free-form
discussion until you stop it.

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
substantive choice it uses a bounded Refine handoff and follows the shared
question rules.
Refine completion alone is not implementation authorization.

For a larger baseline, request To Document and then To Tasks before requesting
implementation of one selected task at a time. A small implementation can finish
with a concise chat result. A requested audit uses Smokes, and acting on its report
uses Fix when explicitly called.

## Split a documented idea into tasks

Invoke `$to-tasks` when you want to split a document into functional or enabling
blocks for later implementation. Reuse one agreed parent Refine baseline; new
substantive choices return through bounded Refine. There is no automatic sequence
from To Document to To Tasks or Implement, and task creation grants no execution
authority.

Each document gets a sibling `[document-name]-tasks` folder. Files start at `00`
with distinct names and stable IDs. Explicit prerequisites determine dependencies.
Every task has an outcome, scope and requirements, scope references, prerequisites,
and acceptance criteria. Exclusions and verification constraints are optional.

Scope references establish meaning and requirements, never permissions; current
boundaries apply independently. Acceptance uses minimal verification; additional
border-value and extreme-case testing is outside this flow. Existing records keep
decisions and blockers rather than duplicating them in task files. Implement
checks actual readiness and executes selected tasks only when requested.

## Create a project-specific skill

Use `$create-skill` to refine the idea and functionality of a local skill first.
It presents the finalized scope and asks whether you agree to implement it.
Yes continues through Implement; No leads to clarification and another Refine
round when needed. Existing relevant refinement and an explicit implementation
request for its presented scope are reused without another approval loop.

New skills default to the selected agent area's `local-skills/<name>/` directory,
normally `Agents/.agents/local-skills/<name>/` in an external project. This is
separate from the release-managed `skills/` directory, so future kit updates do
not own the local skill. An authorized compatible host location may be selected.

The package includes an initializer, metadata generator, and read-only validator.
The initializer previews by default; applying it creates a draft, not a finished
skill. Complete its real instructions and references, validate the result, and
run appropriate permitted checks. Existing folders and metadata are not replaced
by the creation helpers; requested updates preserve unrelated fields and content.

Files created in a project are not automatically installed or discoverable by
the host. Registration, personal installation, entry-file edits, and publication
remain separate actions. The variant retains the upstream license/attribution
and omits optional icons; no binary-asset exception is needed for the kit.

## Read results and resume work

Read accepted decisions and reasons in the designated human topic record.
The caller's separate checkpoint holds operational continuation and references
that record. Refine acts as the caller when invoked directly in the ordinary
workflow. In Orchestrator mode the master maintains the caller checkpoint. Use
one decision record and one checkpoint per topic.

Readable audit/fix reports use the host's report location or the kit's
`docs/reports/` fallback. They link to authoritative JSON under the agent area.
Reports remain historical snapshots; a later correction rechecks current files.

Project Context is a derived view for agents. It does not replace canonical documents,
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

New releases contain `.agents/release/manifest.json` inside the kit, identifying
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

Build with an explicit tag such as `--version v2.3.0`, then publish that same tag
with both `agent-skills.zip` and `agent-skills.zip.sha256` as release assets.
Publication is performed by the user. The repository metadata version alone is
not evidence of a published release. Keep historical assets available while
installed kits may need them to verify baselines. The manifest is embedded in
the ZIP and does not hash itself; the sidecar checksum covers the complete ZIP.

## Layout compatibility

New releases use layout 3 and updater protocol 2. Older published baselines remain
verifiable, but an older updater cannot apply the new namespace directly. Use
standalone Setup for detection/planning and its bundled Update-owned migration
helper for the approved transition. Historical reports retain original evidence.
The local Context skill is now named `project-context`; derived context storage
continues under `.agents/context/`.

Publish `setup.zip` and `setup.zip.sha256` alongside the complete
`agent-skills.zip` and its checksum for this version. Generated bootstrap copies
are packaging outputs; edit their canonical sources and rebuild instead.
