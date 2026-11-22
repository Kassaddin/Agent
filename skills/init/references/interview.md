# Setup Interview

## Local folders

Ask: "Which local repository or project folder should this project use?" Confirm the absolute path and intended role. Supplying a path permits the requested read-only check of that location, not unrestricted inspection of neighboring folders. Check existence and readable metadata without recursively exploring excluded content. Ask about read, create, modify, delete, and execute permissions; show proposed defaults rather than assuming write access from a readable path.

After each folder, ask: "Would you like to add another local folder?" Repeat until no. Establish which folder is primary. Multiple local roots are supported. Add exclusions as narrower sources with prohibitions. Explain that any matching prohibition wins over a broader allowance. Use a directory entry for a tree and a file entry for one file; file entries cannot be recursive.

## Repositories and vaults

Ask for or confirm the remote URL and version-control system for each relevant local repository. Authorized read-only inspection may identify a configured URL; do not assume a remote named origin is the intended source. Never fetch, clone, switch branches, change credentials, or modify version-control configuration merely to discover it.

Ask: "Do you use an Obsidian vault for this project?" If yes, collect its location, establish access, and ask: "Does this vault have a Git or other version-control repository URL?" Register that URL as a separate remote linked by local source ID. Do not infer an Obsidian account, Sync subscription, or version control from the presence of a vault. A remote-only vault source is permitted; do not fabricate a local checkout.

For every remote, including each vault repository, ask: "Should this source be read-only or writable?" Requested mode is an intention; it is not proof of account privileges or permission to make repository changes.

## Access branches

| Requested mode | Result | Next action |
| --- | --- | --- |
| Read | Read succeeds | Record capability read or write, effective mode read, and status ready. |
| Read | No access or unknown | Explain the result and ask whether the user wants access-setup guidance. |
| Write | Write permission verified | Record capability write, effective mode write, and status ready. Version-control rules still apply. |
| Write | Read succeeds but write is absent or unknown | Offer setup guidance. A read-only fallback requires explicit acceptance and becomes status limited. |
| Write | No access | Explain and offer setup guidance. Do not describe the source as usable. |
| Either | Setup declined, no accepted usable fallback | Set effective mode none, status unavailable, and a reason. Retain the source. |

Use authorized account/permission metadata and read-only source checks. A successful read cannot prove write permission. Never create, edit, push, or delete a test artifact to prove write access. If the current tools cannot verify writes, retain capability read if reading was proven, otherwise unknown; record the uncertainty in reason. Record checked_at in ISO 8601 with a timezone when a check was actually attempted, even when the result is unknown.

If anonymous reading succeeds after authenticated access failed and setup was declined, confirm the source will be read-only. A known private source requires valid read access; an inaccessible private source stays unavailable. An HTTP 404 or permission error alone does not establish visibility: use unknown unless verified.

## Granting access

Ask whether the user wants help setting up the failed access. If yes, identify the actual provider and available connector or local authentication method. Consult the provider's current official instructions or connected tool help when needed. Explain the minimum access for the requested mode and give steps the user can perform. Guide account authorization, repository invitation, connector scope, or the user's SSH/credential setup as appropriate. Do not ask the user to paste secrets into chat or YAML.

User-only version-control configuration remains user-performed. Do not silently install a CLI, clone a repository, save credentials, or expand source scopes. After the user says setup is complete, make one authorized read-only recheck and update the state. If it still fails, explain what remains and offer another user-guided attempt or an unavailable entry. Do not retry indefinitely or call an unavailable source during later work without a new request to resolve it.

Each remote uses this complete shape; replace example values and update the states from actual checks. `local_ids` may be empty for a remote-only source. No credentials belong in the URL.

```yaml
- id: project-origin
  url: "https://example.org/team/project.git"
  kind: git_repository
  local_ids: [project]
  requested_mode: read
  effective_mode: none
  access:
    capability: unknown
    status: unchecked
    visibility: unknown
    checked_at: null
    reason: null
  write_approval: ask_each_time
  trust_granted_at: null
```

Use a timezone-bearing timestamp when trust was explicitly granted; otherwise keep trust_granted_at null. An unchecked entry must have effective mode none and capability unknown. Ready means requested mode is available; limited means an explicitly accepted read-only fallback. Unavailable and limited states require a reason. A failed check can retain an unknown capability; it is still an actual attempt, so record its checked_at time.

## Engagement and review

Explain the act/ask/never decisions in the contract and propose the template defaults. Confirm any deviations. Read-only checks are allowed; version-control mutations are user-only; no agent-created branches or PRs; edits stay in the current local checkout. Local content write permission does not permit changing its branch or recording history.

If the user wants quiet delegated Search, offer approvals.allow_read_only_search_worker as a scoped standing approval. Default false, including when the optional field is absent. True satisfies delegation ask only for one bounded read-only Search worker; delegation never and source restrictions still win. Include the exact field in the policy preview before enabling it. Do not enable all delegation to support Search.

Queue notifications apply to local and remote content writes. Remote write approval defaults to each change set. Do not offer persistent trust as a precondition for access setup. Offer it only after the user approves an otherwise permitted remote write, separately from the initial yes. Repository mutations through hosting APIs are still version-control mutations and cannot be enabled by remote trust.

Review sources, requested/effective modes, limitations, local permissions, version-control policy, engagement rules, and destination together. A project with unavailable optional sources can still be activated if the user accepts that limitation. A writable destination for the policy itself must be agreed, or deliver an unsaved draft.
