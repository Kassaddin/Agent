# Repository Agent Guidance

Read `config/BOUNDARIES.yaml` relative to this file and the Init boundary
contract in `skills/init/references/boundary-contract.md` before accessing
project resources. Validate the selected active policy with the trusted installed
Init validator or an explicitly authorized source copy. Reload changed policy
before affected operations. Placement inside `.agents/` grants no additional access. All flows also follow the
shared question/assumption and workflow-economy rules in that boundary contract.

Follow `skills/init/references/project-layout.md`. Reader material belongs in
the existing `docs/` layout. Final documents use its appropriate topic/document
location. Keep machine-specific locations in the boundary configuration, not
in reusable instructions.

Resolve project skill requests from `skills/<name>/SKILL.md` relative to this
file, loading only the relevant instructions/resources. The context skill is
named `project-context`; its derived data remains under `context/`.

The configured vault is read-only, not current, and maintained manually by the
user. The user transfers documents there. Work in the existing local checkout;
all version-control mutations, including pushes, remain user-only. Create no
branches or PRs.

Use Project Context Load when useful for the active request. Its index is
`context/index.yaml` and global view `context/project.md`, relative to this
file. Definitions and decisions remain in their reader-facing canonical files.
Each topic's separate checkpoint is under `state/checkpoints/` and is routed by
the index. Project Context freshness grants neither permissions nor task completion.

Smokes produces reports without correcting inspected files. Fix acts only when
explicitly called. Read-only Search worker approval does not authorize general
delegation or audit/implementation agents.

Generated releases go under `releases/` at the repository root. Include only
allowlisted skill packages and kit guidance in the `Agents/` wrapper; never
package this project's local configuration, context, checkpoints, or reports.
