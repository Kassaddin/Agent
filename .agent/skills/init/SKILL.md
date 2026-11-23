---
name: init
description: Interview the user to establish or update project access, local and remote sources, Obsidian vaults, version-control boundaries, and engagement rules in a validated BOUNDARIES.yaml file.
---

# Init

Follow the shared [project layout](references/project-layout.md) for the selected agent area, established host document locations, separate checkpoints, and report destinations. Adoption does not automatically reorganize host content or overwrite entry files.

Establish the project's operating boundaries through questions and read-only access checks. Produce a uniform, manually editable `BOUNDARIES.yaml`. This skill has no dependency on the glossary or refinement skills: access boundaries must be established before their artifacts are created.

Own boundary configuration and access-policy consistency. Resolve access-policy choices through this setup workflow. When called by another workflow, return the approved configuration, unresolved access, and actual save/validation status so the caller can maintain its continuation and checkpoint.

Read [the boundary contract](references/boundary-contract.md) before interpreting rules and [the interview guide](references/interview.md) when conducting setup. Use [the template](assets/boundaries-template.yaml) and [the schema](references/boundaries.schema.json) to create the file. Use [version-control actions](references/version-control-actions.md) when classifying a command or repository API operation.

## Conduct setup

Use information already provided, but ask the user to confirm consequential choices instead of treating template values as approval. Ask focused questions in stages; do not emit the entire configuration as a questionnaire. Keep this access interview scoped to the requested setup; the refinement skill's dependency-graph discussion is a separate workflow.

1. Ask for a local repository or project folder. Establish its access permissions, check the permitted location, then explicitly ask whether another local folder should be added. Repeat until the answer is no. Identify the primary location.
2. Ask for or confirm its Git or other version-control repository URL. Check read access and, if requested, write privileges without making a test write. On failed access, offer setup guidance. A declined setup can leave a repository as read-only only if reading actually succeeds; otherwise record it as unavailable. Notify the user when it is known to be private; do not infer privacy from an access error alone.
3. Ask whether an Obsidian vault is involved. If yes, record its local folder or remote location and ask whether it has a version-control URL. A vault without version control is valid. Relate each remote to the appropriate local source IDs.
4. For every remote source, ask for read or write mode. Follow the guide's access/setup branches, record both the requested mode and verified effective mode, and retain declined or inaccessible sources with an explicit unavailable state and reason. Do not silently omit them.
5. Confirm engagement and version-control defaults, source exclusions, and how change notifications and approvals work. Show the completed draft with unresolved access clearly marked.

If Search workers are wanted, explain the optional `approvals.allow_read_only_search_worker` flag. Default it to false; true is a scoped standing approval for one bounded read-only Search worker, not permission for general delegation. Apply the contract's Search approval rules and record true only after an explicit reviewed choice.

Read-only checks are allowed within the authorized sources. Version-control mutations remain user-only by default, including staging, fetches, commits, configuration changes, branch switching, and pushes. Create no branches or PRs. Work only in the existing local checkout and branch. Authentication changes, installations, cloning, and permission grants require a separate user-authorized step; provide guidance for the user rather than silently performing them.

## Validate and activate

Build the draft from the user's answers. Keep `state: draft` until the user approves the concrete configuration. Do not save passwords, tokens, private keys, credential-bearing URLs, or authentication output. Preserve unavailable sources and uncertainty instead of claiming setup succeeded.

Validate with Python and PyYAML available:

```text
python <init-skill-folder>/scripts/validate_boundaries.py <path>/BOUNDARIES.yaml
```

The validator performs no network requests, permission grants, Git operations, or source traversal. Its dependency is listed in [requirements.txt](scripts/requirements.txt). Fix errors, explain meaningful warnings, and present the intended destination and any project-guidance changes for review. If Python or PyYAML is missing, report validation as incomplete; do not install dependencies without authorization or claim a validated activation.

After approval, set `state: active`, validate with `--require-active`, and save under the selected agent area's `config/BOUNDARIES.yaml` unless an existing explicit policy location was retained. Preserve any existing file and concurrent edits. For read-only planning, provide the draft in chat instead of activating it.

For discovery, reuse the host's existing entry mechanism. Offer a small pointer in its existing `AGENTS.md` only when needed and explicitly authorized; adopting the release does not edit or create a host entry file automatically. Show that addition in the activation preview, use a concrete installed contract location, and preserve unrelated instructions. Do not recursively modify guidance in every source folder or create an instruction hierarchy without agreement.

## Update and remote-write trust

For an existing configuration, read and validate it first, ask only about affected choices, and show the proposed changes. Recheck access when the account, endpoint, or permissions change. A manual edit must be reloaded and validated before the next affected operation.

With the default approval settings, notify the user about queued changes to writable local and remote sources before applying them. For an otherwise permitted remote write, request approval for that source and change set. After yes, offer **Do not ask again for this source**. Record `trusted_for_source` only after that separate explicit choice; otherwise keep `ask_each_time`. Apply explicitly amended approval flags as defined in the contract. Trust is scoped to the configured source and project, is revocable, and does not expand task scope or override user-only version-control actions. If the policy file cannot be updated, report persistence as pending rather than claiming remembered trust.
