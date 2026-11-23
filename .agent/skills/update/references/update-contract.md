# Update Contract, Protocol 1

## Managed inventory and baseline

A managed file is a kit file in a verified published inventory. An installed baseline is a verified release identity and its original file inventory. A release manifest is the versioned inventory containing identity, compatibility requirements, and managed-file hashes. These names remain proposed glossary entries until explicitly agreed; their operational boundaries here are defined for this protocol.

The bundle ID is `agent-skills`. A manifest has exactly `format_version: 1`, `bundle_id`, SemVer-tag `version`, `layout_version: 2`, `min_update_protocol: 1`, `skills`, and `files`. Each file entry has `path`, lowercase SHA-256, and byte count. Each listed skill needs its matching `SKILL.md`. File references are canonical portable paths relative to the kit root.

Allowed payloads are `.agent/skills/<skill>/...`, `README.md`, `docs/guide.md`, `.agent/instructions.md`, and `.gitignore`. The manifest itself is `.agent/release/manifest.json`; it is not listed in its own inventory and contains no archive hash. Protected local configuration/state/context/reports and arbitrary host paths cannot be declared managed by a release. ZIP entries have a single `Agents/` wrapper; symlinks, path traversal, duplicate/case-colliding paths, directory/file collisions, oversized data, and encrypted entries are rejected.

The complete ZIP is covered by `agent-skills.zip.sha256`. Publisher asset digests, when present, must agree. The manifest version must equal the published tag. Baseline receipts at `.agent/state/update/receipt.json` reference release/asset IDs, repository identity, archive hash, and manifest hash rather than duplicating per-file inventories. The current manifest and receipt are checked against the published baseline; a receipt is never a permission grant.

With no receipt, an installed manifest is checked against its published package. Legacy wrapped packages can supply a derived baseline only when their published ZIP/checksum and current files establish a match. Search is bounded to three visible published candidates; absence within that bound is not exhaustive absence. An explicit baseline tag avoids guessing. Unknown or ambiguous baselines stop application.

## Comparison and compatibility

Compare baseline, current files, and candidate. Retain unmanaged files. Occupied new paths are conflicts even when bytes happen to match, because ownership cannot be silently adopted. Changed baseline files are conflicts unless already identical to the selected candidate, including an already absent retired file. Never automatically merge local edits or claim success for a mixed bundle.

Default selection is the provider's latest stable published release. An explicit published version permits intentional pinning, including a downgrade; an unrequested downgrade stops. Changed archive bytes under the same version stop for a producer/version decision. Unsupported layout/protocol, invalid metadata/syntax, or unresolved local links stop before managed writes. No dependency or migration script from the candidate is executed. Detailed semantic correctness and external-service behavior are not proved by these checks.

## Access and downloads

All operations use current active boundaries, overlapping lexical/resolved restrictions, primary-project scope, and approved source identity. The target is an installed kit workspace, not the development repository or a personal installation. Its own `Agents/` directory may be the primary permitted root; no surrounding host access is then implied. Paths cannot cross kit symlinks/junctions. The helper performs no Git command and no repository mutation.

The GitHub adapter uses GET-only release/latest, release-by-tag, release lists, and release-asset endpoints. It validates the repository/asset association, supports direct binary responses and provider redirects, strips authorization on host changes, and limits redirects to HTTPS GitHub delivery hosts. Existing `GH_TOKEN`/`GITHUB_TOKEN` values may be used without storing or printing them. Authentication setup and source-policy amendments remain user/Init work.

Limits: 32 MiB compressed download, 64 MiB total expanded content, 8 MiB per file, 2,001 ZIP entries, 20-second requests within a 120-second adapter budget, and at most three automatic baseline candidates. Limit failures are explicit, not negative search results. A missing latest endpoint alone does not establish no releases; a readable published-release list distinguishes no stable release from inaccessible data.

Provider behavior: [GitHub release endpoints](https://docs.github.com/en/rest/releases/releases) and [asset downloads](https://docs.github.com/en/rest/releases/assets). The source and checksum establish the inspected published artifact, not universal correctness or permission to run its code.

## Application, interruption, and outcome

Checks do not write. Application requires the previewed archive hash, an explicit caller request, required notification, and actual permissions. `--approve operation:project-relative-path` represents already-granted ask approval; the caller must not invent it. Never and resolved-scope restrictions still win.

The updater owns its lock, current receipt/pending pointer, bounded run journal/backups, and immutable outcomes. [Setup](../../setup/SKILL.md) establishes the first installed receipt using this same protocol. A pending Setup journal requires Setup recovery before Update; it is not an older-kit baseline to guess or overwrite. A lock prevents concurrent updater commits. Before managed writes, preflight actual destinations and report paths, capture backups, and reserve the pending run. Recheck every target before changing it; write the manifest/receipt with the coherent candidate and verify bytes. The running updater uses its already-loaded trusted implementation, not newly installed instructions.

On interruption, no later update proceeds until recovery is resolved. Recovery restores only recorded updater writes whose current bytes still match the written value, or recognizes already-restored originals. It validates backup hashes and never overwrites unrelated concurrent changes. Missing delete/create rights or indeterminate partial content can require user action; report `recovery_required` without claiming success. A verified committed run with interrupted bookkeeping is recognized without rolling back its successful update.

Structured outcomes are under `.agent/reports/update/<attempt>/outcome.json`; reader outcomes use the host's established report location or kit `docs/reports/update/<attempt>/outcome.md`. Each representation shares status/version/details and links to the JSON. Recovery creates a new outcome and retains old evidence. The journal is execution/recovery state, not another decision record or topic checkpoint.
