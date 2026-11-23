# Version-Control Action Mapping

Use effects, not command spelling. A command can require multiple policy operations in addition to local/remote resource permissions.

| Policy operation | Git examples or equivalent effects |
| --- | --- |
| inspect | Status, diff, log, show, reading remotes, ls-remote, read-only provider metadata |
| stage_changes | Add, unstage, index changes |
| record_changes | Commit, amend |
| create_branch | Branch creation through CLI or hosting API |
| create_worktree | Worktree add/remove |
| switch_revision | Checkout, switch, changes to the active revision |
| retrieve_remote_changes | Fetch; modifies local repository metadata |
| integrate_changes | Merge, cherry-pick, pull's integration step |
| rewrite_local_history | Rebase, amend, history rewriting |
| discard_local_changes | Restore/discard, stash operations that modify local work |
| remove_untracked_files | Clean, including destructive preview-to-execution workflows |
| reset | Reset of any mode; may also stage, discard, or rewrite history |
| publish_changes | Push; repository file create/edit/delete through a hosting API |
| overwrite_remote_history | Force push, deleting/rewriting published history |
| change_configuration | Config, remote changes, credential configuration, hooks |
| create_pull_request | PR or merge-request creation through any interface |

Default all mutation operations to user_only, except create_branch and create_pull_request to never. A separate explicit boundary amendment is needed to change these policies. Normal task approval or remote-write trust does not do so.

Prefer checks that do not update the index or other metadata, such as Git's no-optional-locks mode for status. Do not equate a command's dry-run label with absence of effects without checking its behavior. Fetch and pull are not read-only checks. Do not run git init, clone, tag mutation, repository administration, or an unmapped mutation under inspect: apply unmatched_operation and resource rules, and the default user-only mutation rule. Follow the same rule for other version-control systems; do not guess their command semantics.

Examples: pull requires retrieve_remote_changes and integrate_changes; amend requires record_changes and rewrite_local_history; a provider API file edit requires publish_changes and remote write capability. An SVN commit both records and publishes changes. Refuse agent execution when any applicable operation is user_only or never.
