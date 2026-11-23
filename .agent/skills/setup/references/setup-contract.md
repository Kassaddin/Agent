# First Installation Contract

## Authority and shared format

Setup is a first-installation workflow for local use and limited sharing. The fixed repository is `https://github.com/Kassaddin/Agent`. Downloads use Update's GET-only GitHub adapter, bounds, checksum/tag/manifest checks, safe-path rules, syntax checks, and dependency-link validation from the [Update contract](../../update/references/update-contract.md). No second release format or verifier is maintained.

The current complete kit requires Backlog, Context, Create Skill, Fix, Glossary, Implement, Init, Refine, Search, Setup, Smokes, To Document, To Tasks, and Update. Install every inventoried file, including additional compatible skills, with all four kit guidance files. A package omitting a required skill is incompatible with this Setup version. Future retirement of one requires revising this requirement. No downloaded code is executed by Setup.

With an active boundary policy, use Update's shared path/access checks and the fixed repository's explicitly configured readable source. A selected explicit policy is retained; absent discovery does not create a competing policy. Revalidate after changes. An existing policy must cover installation and investigation; setup does not amend it. A bootstrap grant is available only when neither an explicit policy nor a known candidate is present. It covers fixed-source reads and the new `Agents/` tree, its records, and cleanup of identified unchanged Setup writes; it grants no surrounding host traversal, Git operation, authentication change, or lasting policy.

## First installation and records

The host directory must exist. The only destination is its direct child `Agents/`. Reject linked/junction paths in the host ancestry or kit. Existing destinations, including empty directories, are conflicts. An installed kit routes to Update only on an explicit update request; occupied/unverified destinations require a user decision. No force or automatic merging exists.

Preview is read-only. Apply requires the previewed hash, pinned tag, notification, and current authorization. Reserve the destination with exclusive directory creation before writing. Keep an exclusive per-run process lock and journal at `.agent/state/setup/journal.json`. Preflight writes and report destinations before reservation. A pending journal blocks fresh installation and Update; use Setup recovery first.

Install the complete payload and manifest, then the initial `.agent/state/update/receipt.json`, using the shared receipt schema and the verified published identity. Update remains accountable for the receipt protocol and later maintenance; Setup only establishes its initial value. Hash-check written bytes before marking installation verified. Structured outcomes are immutable under `.agent/reports/setup/<attempt>/outcome.json`; reader outcomes are derived from that data under `docs/reports/setup/<attempt>/outcome.md` within the kit, linked to the JSON.

Failure leaves a bounded journal and attempts cleanup only when current permissions permit it. Recovery never downloads or executes a package. It validates paths/hashes and identifies Setup-created files by recorded filesystem identity and expected bytes. Unrecorded, partially written, replaced, or concurrently edited files are preserved for inspection. Empty installation directories may remain; recovery does not recursively delete the kit or host content. An existing recovered folder needs an explicit user decision before another installation. If all intended bytes verify after an interrupted finalization, finish the installation record rather than roll back a complete kit. A committed installation that later drifted is preserved and reported, not removed.

## Boundary continuation and completion

The helper reports `init_required` when discovery finds no policy and `ask_init` for a present selected/unambiguous policy. Multiple candidates report `select_boundaries`. This is presence-based routing, not a claim of valid permissions. The agent conducts the handoff: no policy means start Init automatically; a present policy means ask. Initial activation always requires Init's concrete user-approved policy and validation. Extraction alone performs no activation.

Report installation and activation separately. Setup can finish with verified installation and pending activation if Init is blocked or declined. Never claim the project is configured from the receipt, folder placement, or a successful download. Host integration, personal skill discovery/installation, Context building, Git mutations, publication, multiple providers, and selective packages are outside this MVP.
