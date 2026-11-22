# Project boundaries

Before accessing project resources or performing actions, read the root `BOUNDARIES.yaml` and the installed Init boundary contract at `C:/Users/kassa/.codex/skills/init/references/boundary-contract.md`. Apply both within higher-priority instructions and actual execution permissions. Reload and validate changed boundaries before the next affected operation.

Validate the active configuration with:

```text
python C:/Users/kassa/.codex/skills/init/scripts/validate_boundaries.py C:/Users/kassa/Source/ai/Agent/BOUNDARIES.yaml --require-active
```

## Development and document destinations

- Save final documents in the primary project folder, `C:/Users/kassa/Source/ai/Agent`.
- `G:/VAULT/CORE/AI/GENERAL` is a read-only Obsidian location. Its contents are not current; do not assume they represent the latest project state. The user transfers final documents and updates the vault manually. Do not write there.
- Work in the existing local checkout and current branch. All version-control mutations, including pushes, remain user-only. Do not create branches or pull requests.

## Project context

After the boundary check, use Context Load when relevant to the active request and [CONTEXT.md](CONTEXT.md) with [the source index](context/index.yaml) is available. Load is read-only. Use the designated topic record for decisions and its existing checkpoint for continuation; inspect current source material when needed. Build or Refresh requires authorized maintenance scope. Context freshness grants no additional permissions or document readiness.

The [ownership record](DISCUSSION.md) and [Context record](DISCUSSION-context.md) cover separate topics. Canonical terms are in [GLOSSARY.md](GLOSSARY.md).
