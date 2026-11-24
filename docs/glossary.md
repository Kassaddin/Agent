# Glossary: Agent Skills

Scope: Shared terminology of this project's fourteen reusable skills: `setup`, `init`, `glossary`, `refine`, `backlog`, `implement`, `create-skill`, `search`, `to-document`, `to-tasks`, `smokes`, `fix`, `project-context`, and `update`. Definitions apply to their access, discussion, backlog-capture, implementation, document, task-decomposition, audit, correction, project-context, kit-installation, and kit-update workflows across topics.

Agreed terms reflect explicit discussion agreements or meanings already specified in the approved skill contracts. Proposed terms are definitions inferred from current usage; their labels or boundaries still need agreement. Operational procedures and project decisions remain in the skills and `BOUNDARIES.yaml`.

Agreement status and entry format follow [Glossary](../.agents/skills/glossary/SKILL.md#resolve-meanings) and its [entry rules](../.agents/skills/glossary/references/glossary-format.md#entry-rules).

## Agreed terms

### Refinement and document preparation

#### MVP

The smallest coherent version of the intended outcome, with complete coverage of the agreed initial scope and requirements.

Alias: minimum viable product. Scope: personal, creative, organizational, academic, and technical outcomes in this workflow.

Sources: [Refine](../.agents/skills/refine/SKILL.md#refine-ideas), [To Document](../.agents/skills/to-document/SKILL.md#to-document). The discussion explicitly established "minimal yet full."

#### MVP baseline

The refined description of an MVP, including its requirements, decisions, and limits.

Qualifier: For a question or decision, the baseline may be a reasoned answer or decision framework.

Source: [Refine](../.agents/skills/refine/SKILL.md#refine-ideas).

#### Small task

A task with bounded scope, identifiable dependencies, and a result that can be verified directly against its agreed requirements.

Source: Explicit user definition during Implement refinement on 2026-11-23; [accepted decision I2](topics/implement/decisions.md#i2-any-topic-with-criterion-based-suitability).

#### Functional block

A coherent part of the documented scope with a distinct functional or enabling outcome that can be verified once its prerequisites are satisfied.

Sources: Explicit user agreement during To Tasks refinement on 2026-11-23; [accepted decision T2](topics/to-tasks/decisions.md#t2-functional-and-enabling-blocks), [To Tasks](../.agents/skills/to-tasks/SKILL.md#establish-scope-and-access).

#### Substantive gap

Missing, conflicting, or ambiguous information necessary to establish the document's meaning, required coverage, or conclusions.

Source: [To Document](../.agents/skills/to-document/SKILL.md#to-document); this definition was explicitly accepted in the discussion.

#### Dependency graph

The network of unresolved discussion questions and their prerequisite relationships, including questions with several prerequisites.

Avoid: dependency tree, when it implies that each question has only one prerequisite.

Source: [Refine](../.agents/skills/refine/SKILL.md#work-through-a-dependency-graph); "dependency graph" was explicitly accepted in the discussion.

#### Question round

A group of mutually independent discussion questions whose prerequisites are sufficiently established for meaningful answers in that round.

Source: [Refine](../.agents/skills/refine/SKILL.md#work-through-a-dependency-graph).

#### User context

Personal or situational information supplied by the user, including circumstances, experiences, intentions, values, preferences, and constraints. It may contain factual claims whose attribution and verification are distinct from the user's preferences or choices.

Source: [Refine](../.agents/skills/refine/SKILL.md#find-facts-and-obtain-context).

#### Faithful synthesis

A representation of established source material with its meaning, agreement status, and necessary qualifications preserved.

Source: [To Document](../.agents/skills/to-document/SKILL.md#write-a-faithful-complete-synthesis); faithful synthesis was explicitly selected in the discussion.

### Ownership and handoffs

#### Owner

The skill responsible for the meaning, consistency, and maintenance of a specified kind of information or artifact.

Sources: [Accepted decision D1](topics/ownership/decisions.md#d1-owner-and-ownership-map), [shared ownership contract](../.agents/skills/refine/references/ownership-contract.md#owners-and-corrections).

#### Mechanical correction

A correction whose intended result is unambiguously supported by current authoritative material and preserves agreed meaning, scope, and requirements.

Sources: [Accepted decision D2](topics/ownership/decisions.md#d2-accountable-owner-and-mechanical-corrections), [shared ownership contract](../.agents/skills/refine/references/ownership-contract.md#owners-and-corrections).

#### Resume checkpoint

A compact record of the active request, relevant decision references, current step, blockers, pending artifact updates, and next action.

Sources: [Accepted decision D6](topics/ownership/decisions.md#d6-resume-checkpoint), [shared ownership contract](../.agents/skills/refine/references/ownership-contract.md#resume-checkpoint).

### Project Context and layouts

#### Project context

A maintained, source-linked view of the project's current objective, scope, state, relevant decisions, and unresolved matters.

Sources: [Project Context decision C1](topics/context/decisions.md#c1-context-ownership-and-operations), [Project Context contract](../.agents/skills/project-context/references/context-contract.md#ownership-and-flow).

#### One context view

One coherent project orientation with references to the necessary source records.

Sources: [Project Context decision C4](topics/context/decisions.md#c4-layout-by-retrieval-needs), [layout contract](../.agents/skills/project-context/references/context-contract.md#layout-choices).

#### Context views by area

A layout with separate focused area views for complete task-relevant state and selective retrieval.

Qualifier: The 700-word global orientation budget is an advisory starting trigger, alongside independently changing areas and repeated focused extraction needs; it is not a source-reading limit.

Sources: [Project Context decision C4](topics/context/decisions.md#c4-layout-by-retrieval-needs), [layout contract](../.agents/skills/project-context/references/context-contract.md#layout-choices).

### Access and retrieval

#### act

An authorization decision permitting an agent operation within a requested task and matching resource permissions.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#decisions-and-approvals).

#### ask

An authorization decision contingent on specific user approval for the operation and affected resources, including an applicable approval already given.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#decisions-and-approvals).

#### never

A prohibition on an agent operation under the active boundary policy.

Qualifier: Ordinary action approval is not a policy amendment.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#decisions-and-approvals).

#### user_only

A reservation of an operation for the user, with agent execution prohibited under the active policy.

Scope: Version-control operations in the current boundary contract.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#decisions-and-approvals).

#### Read-only source

A configured source whose authorized agent content access permits reading and excludes content changes.

Qualifier: A writable local checkout and its read-only remote are separate configured sources.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#match-resources-and-effects).

#### Requested mode

The user's selected read or write access intent for a remote source.

Field: `requested_mode`.

Sources: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#match-resources-and-effects), [access branches](../.agents/skills/init/references/interview.md#access-branches).

#### Verified capability

The access capability established for the account and tools at the recorded remote-access check, independently of the user's authorization to use it.

Field: `access.capability`; `none` denotes no access, `read` and `write` denote those capabilities, and `unknown` denotes an unestablished capability.

Sources: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#match-resources-and-effects), [access branches](../.agents/skills/init/references/interview.md#access-branches).

#### Effective mode

The recorded usable remote access level consistent with verified capability and the user's accepted access choice.

Field: `effective_mode`; values: `none`, `read`, `write`.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md#match-resources-and-effects).

#### Remote access status

The recorded state of a remote source's access verification and accepted usability.

Field: `access.status`.

- `unchecked`: no recorded access-check attempt; capability is unknown and effective mode is none.
- `ready`: verified usable access matching the requested mode.
- `limited`: an explicitly accepted read-only fallback for requested write access.
- `unavailable`: no accepted usable access; effective mode is none.

Source: [Init access branches](../.agents/skills/init/references/interview.md#access-branches).

#### Search worker

A bounded, read-only agent assigned one Search request within authorized sources.

Alias: Search agent. Qualifier: Search also permits direct lookup under its contract; worker delegation has its own permission requirements.

Sources: [Search](../.agents/skills/search/SKILL.md#boundaries-and-worker), [scoped Search approval](../.agents/skills/init/references/boundary-contract.md#scoped-search-approval).

#### Search result

A structured retrieval record for a bounded query, containing its status, matches, verified locators where available, coverage, and limitations.

Status values are scoped to Search:

- `complete`: the stated search scope completed with matches and no material coverage gaps.
- `no_matches`: the stated scope completed without matches or material coverage gaps.
- `partial`: limits, exclusions, errors, or unsearched requested sources prevent complete coverage.
- `blocked`: no requested source was searchable because of policy or unavailable access.
- `error`: an input, dependency, configuration, or search-engine failure prevented the operation.

Source: [Search worker result contract](../.agents/skills/search/references/worker-contract.md#result).

#### Coverage

The recorded extent and status of an investigation within a stated scope, including omissions and limitations.

Qualifier: Search coverage concerns sources and queries; Smokes coverage concerns checks and inspected paths. A complete status applies to the stated scope and check.

Sources: [Search results](../.agents/skills/search/references/worker-contract.md#result), [Smokes scope and coverage](../.agents/skills/smokes/references/report-contract.md#scope-and-coverage).

### Audit and correction

#### Smokes report

An immutable audit record containing its scope, captured file states, coverage, findings, and advised remediation.

Representation: Structured JSON is authoritative; supplied Markdown is derived from the same data.

Source: [Smokes report ownership](../.agents/skills/smokes/references/report-contract.md#ownership-and-delivery).

#### Finding

A report entry for one distinct issue or matter requiring review, with evidence, impact, correction criteria, and remediation constraints.

Source: [Smokes findings and counts](../.agents/skills/smokes/references/report-contract.md#findings-and-counts).

#### Certainty

The classification of a finding's evidential support and unresolved interpretation, independent of its remediation requirements.

- `confirmed`: reproducible evidence establishes the defect.
- `needs_review`: intent or interpretation remains unsettled.

Qualifier: A confirmed defect can still require a user decision about its correction.

Source: [Smokes findings and counts](../.agents/skills/smokes/references/report-contract.md#findings-and-counts).

#### Severity

The classification of a finding's impact on the intended workflow or agreed requirements.

- `critical`: workflow unusable or an explicit boundary violated.
- `high`: a required behavior broken.
- `medium`: partial failure or material inconsistency.
- `low`: limited clarity or maintenance concern.

Source: [Smokes findings and counts](../.agents/skills/smokes/references/report-contract.md#findings-and-counts).

#### Priority

The advised timing or order of remediation, assessed independently of severity.

- `P0`: immediate.
- `P1`: before affected use.
- `P2`: scheduled.
- `P3`: optional or low urgency.

Source: [Smokes findings and counts](../.agents/skills/smokes/references/report-contract.md#findings-and-counts).

#### Remediation mode

The classification of a finding's current correction constraints, including permission and unresolved intent.

- `agent_candidate`: a candidate agent correction consistent with current local permissions; a separate Fix request and successful verification remain necessary.
- `user_action`: a correction outside current agent write permissions.
- `decision_required`: an unresolved meaning or content choice necessary to determine the correction.

Scope: The `remediation.mode` field in a Smokes report; these values are distinct from Fix outcome statuses.

Source: [Smokes findings and counts](../.agents/skills/smokes/references/report-contract.md#findings-and-counts).

#### Fix outcome

A separate correction record linked to a Smokes report ID, accounting for each selected finding's disposition, changed locations, verification evidence, and remaining user action.

Status values:

- `verified_fixed`: the finding's acceptance check passed against current content.
- `already_resolved`: current evidence establishes that the finding no longer reproduces.
- `needs_user_decision`: an unresolved user choice prevents a supported correction.
- `blocked_access`: unavailable access or privileges prevent the correction.
- `user_action_required`: a necessary action remains assigned to the user.
- `failed_verification`: the attempted correction has not passed its acceptance check.

Sources: [Fix verification](../.agents/skills/fix/SKILL.md#verify-and-account-for-every-finding), [Smokes Fix handoff](../.agents/skills/smokes/references/report-contract.md#fix-handoff-and-freshness).

## Proposed terms

### Project-local authoring

#### Project-local skill

A project-specific skill stored outside the published kit's managed inventory.

Needs agreement: This exact glossary wording remains proposed; the selected Create Skill workflow defines the operational destination and ownership.

Source: [Create Skill](../.agents/skills/create-skill/SKILL.md#scope-and-destination).

### Deferred work

#### Backlog

A project's single record of topics and potential work retained for later consideration because they fall outside the discussion or task's current scope.

Needs agreement: This exact glossary wording remains proposed; the operational capture rules follow the accepted Backlog baseline.

Sources: [Backlog](../.agents/skills/backlog/SKILL.md#backlog), [accepted capture decision B1](topics/backlog/decisions.md#b1-automatic-capture-with-scope-clarification).

### Document preparation

#### Writing brief

The working specification of a document's purpose, audience, required coverage, document type, language, detail level, format, and destination.

Needs agreement: Whether this is the canonical term for the combined writing requirements and which elements are essential in every case.

Source: [To Document](../.agents/skills/to-document/SKILL.md#establish-the-writing-brief).

#### Source material

The information basis for a document, including supplied material, verified retrieved evidence, and decisions established through Refine.

Needs agreement: The boundary between material available for consideration and material established as the document's authoritative basis.

Source: [To Document](../.agents/skills/to-document/SKILL.md#resolve-gaps-and-resume).

#### Substantive user choice

A user-owned choice that materially affects the objective, scope, priorities, constraints, required coverage, or conclusions.

Needs agreement: The precise boundary from routine editorial choices and requests for already-known user context.

Sources: [Refine decisions](../.agents/skills/refine/SKILL.md#work-through-a-dependency-graph), [To Document gap resolution](../.agents/skills/to-document/SKILL.md#resolve-gaps-and-resume).

#### Routine editorial choice

A presentation choice within the writing brief that preserves the established substance and required coverage.

Needs agreement: Which changes of title, structure, tone, or emphasis remain editorial when they could affect a reader's interpretation.

Source: [To Document](../.agents/skills/to-document/SKILL.md#establish-the-writing-brief).

#### Document readiness

The state of a writing brief and its source material with every substantive gap resolved for the requested document.

Needs agreement: This name for the pre-drafting state, distinct from an MVP baseline's completeness and the finished document's verification.

Sources: [To Document readiness](../.agents/skills/to-document/SKILL.md#establish-readiness-before-drafting), [Refine completion](../.agents/skills/refine/SKILL.md#assess-completion-and-deliver-the-baseline).

#### Established fact

A factual claim with evidence sufficient for its stated use in the current discussion or document.

Needs agreement: The evidence threshold for this classification, including its distinction from a retrieved source claim or attributed user context.

Sources: [Refine facts and context](../.agents/skills/refine/SKILL.md#find-facts-and-obtain-context), [To Document readiness](../.agents/skills/to-document/SKILL.md#establish-readiness-before-drafting).

### Boundary terminology

#### Boundary configuration

The project-specific record of sources, operation decisions, version-control rules, and approval preferences in `BOUNDARIES.yaml`.

Needs agreement: This canonical name for the configured project rules, distinct from the shared interpretation contract; current skills often use "boundaries" for this record.

Source: [Init boundary discovery](../.agents/skills/init/references/boundary-contract.md#discovery-and-bootstrap).

#### Boundary contract

The shared specification of a boundary configuration's interpretation and application across skills.

Needs agreement: This definition of the existing contract label and its distinction from a project-specific boundary configuration.

Source: [Init boundary contract](../.agents/skills/init/references/boundary-contract.md).


### Kit updates

#### Managed file

A file belonging to the kit's verified distributable inventory.

Needs agreement: This canonical name and its inventory-based ownership boundary.
Source: [Update contract](../.agents/skills/update/references/update-contract.md#managed-inventory-and-baseline).

#### Installed baseline

The verified release identity and original file inventory for the kit currently being updated.

Needs agreement: This canonical name for the comparison basis, distinct from the current edited files.
Source: [Update contract](../.agents/skills/update/references/update-contract.md#managed-inventory-and-baseline).

#### Release manifest

The versioned inventory of a published kit release, including its identity, compatibility requirements, and managed-file hashes.

Needs agreement: This canonical name for the release inventory, distinct from the local installed receipt.
Source: [Update contract](../.agents/skills/update/references/update-contract.md#managed-inventory-and-baseline).
