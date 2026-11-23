---
name: setup
description: Install the complete project-local Agents kit from this skill set's fixed published-release repository, verify its initial baseline, and continue into Init when project boundaries are absent.
---

# Setup

Own first installation and its verified outcome. Install the complete kit into the selected local project's `Agents/` folder. The MVP uses only published releases from `https://github.com/Kassaddin/Agent`; there is no source override, clone, branch archive, selective installation, or personal skill installation.

Read the shared [boundary contract](../init/references/boundary-contract.md), [layout contract](../init/references/project-layout.md), and [setup contract](references/setup-contract.md). Use the existing trusted [helper](scripts/setup_kit.py), which reuses Update's release adapter, content verification, and receipt format. Do not run candidate scripts or reload downloaded instructions during installation.

The helper needs Python 3.10+ and PyYAML 6.x, plus the sibling Update, Smokes, and Init packages. Missing dependencies block verified installation; explain the missing prerequisite without installing it automatically.

## Resolve installation authority

Identify the host project folder from the request or existing context; ask only if unclear. Inspect the known boundary candidates or use the explicitly selected policy. An existing policy must be active, valid, and sufficient for this source and destination. Multiple candidates require selection. Invalid or draft files cannot be bypassed with bootstrap authorization; refer access-policy problems to Init.

When no policy exists, explain the exact fixed source and `<project>/Agents` destination and obtain explicit authorization to inspect/download that release and create/verify the kit and its local installation records. `--bootstrap-approved` represents that actual scoped authorization, including bounded cleanup of Setup's own unchanged writes; it is not a persistent policy or permission to inspect the host's other content. An invocation without a clear destination is insufficient. Keep platform permission gates separate.

## Verify before writing

Use the latest stable published release unless a published version was explicitly requested. Start with a non-writing check:

```text
python -B <setup-folder>/scripts/setup_kit.py --project-root <host> --boundaries <selected-policy> --source <configured-source-id>
```

For an authorized first installation without a policy, replace the boundary/source arguments with `--bootstrap-approved`. The source remains fixed. Stop on missing release assets, incompatible/incomplete inventory, invalid content/links, or inaccessible source; explain the specific blocker without substituting another source.

An existing `Agents/` directory is never merged or adopted. If it is a verified installed kit, return its location for an explicit Update request. Otherwise ask about the occupied destination. An interrupted Setup run uses `--recover`, not Update or a fresh installation.

Notify the user of the selected version, destination, and additions before applying. Pin both the resolved version and previewed archive hash:

```text
python -B <setup-folder>/scripts/setup_kit.py --project-root <host> --boundaries <selected-policy> --source <configured-source-id> --version <resolved-tag> --apply --expected-sha <preview-sha256> --notified
```

Use `--approve operation:project-relative-path` only for actual scoped ask approval under the selected policy. Never/user-only restrictions still apply. The helper creates a new destination exclusively, records progress, verifies the complete written inventory, and writes the initial receipt under Update's contract. Recovery preserves concurrent changes and reports unresolved cleanup; it never claims an incomplete installation succeeded.

## Continue into Init

After verified installation, discover boundary files again through the layout contract. **If none is present, start [Init](../init/SKILL.md) automatically. If one is present, ask whether the user wants to run Init.** Multiple candidates require selection first. Reuse the known project, installed kit, release source, and scoped authorization as context; do not treat installation authorization as answers to Init's policy questions.

Init still owns the interview, concrete policy preview, user approval, validation, and activation. Declining Init preserves the existing configuration; an invalid/inactive file remains unusable. Missing Python/PyYAML or declined policy approval leaves activation pending. Host entry-file changes require their own authorized preview. The helper returns the required continuation but never conducts an interview, creates boundaries, installs dependencies, or changes credentials itself.

Pass the fixed repository as the kit's release source, separately from the host project's own Git remote. Do not substitute the distribution repository for the project's repository or overwrite an existing source mapping.

## Return

Report version, kit location, verification, linked JSON/reader outcome, and boundary status separately. An installed kit awaiting Init is installed but not configured. Preserve the caller's continuation and the [ownership contract](../refine/references/ownership-contract.md); substantive choices use Refine, access-policy choices use Init. Do not publish, run Git mutations, update an existing kit, or synchronize personal skill copies.
