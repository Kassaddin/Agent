---
name: implement
description: Execute an agreed Refine baseline for a small task on any topic, verify the result directly, and pause the task for unanswered user questions without requiring a document-production flow.
---

# Implement

Own authorized execution, verification evidence, and the implementation outcome. Work from an agreed [Refine](../refine/SKILL.md) baseline, which may be in the conversation or the topic's designated decision record. A standalone clear request without an agreed Refine baseline is not this skill's input; use Refine to establish agreement before implementing.

## Resume and check readiness

Read the shared [boundary contract](../init/references/boundary-contract.md), current selected policy, [layout contract](../init/references/project-layout.md), and [ownership contract](../refine/references/ownership-contract.md). Apply them to sources, actions, delegation, and state. Missing boundaries permit only existing explicit authorization; never invent permissions or start Init automatically. Access-policy choices belong to Init.

Use [Glossary](../glossary/SKILL.md) to reuse the baseline's agreed terminology and preserve proposed meanings. Assess a small task by **bounded scope, identifiable dependencies, and direct verification against agreed requirements**. Do not impose file, line, or duration thresholds. When these properties cannot be established, return the specific scope or readiness gap to Refine instead of silently broadening the task or forcing To Document.

Recover the relevant requirements, decisions, constraints, affected resources, and completion criteria from existing sources. Use Context Load when useful and [Search](../search/SKILL.md) for factual retrieval under its worker and access rules. Check current resource state before changing it; summaries and old checkpoints do not prove present state. Missing required contracts or dependencies block affected work; asking the user a question pauses the whole task under the boundary contract.

## Execute the agreed work

Require an explicit implementation request for the agreed baseline, such as an Implement invocation or a clear request to carry it out. Agreement or Refine completion alone is not execution authorization. A current authorization needs no repeated blanket confirmation; notify changes and handle actual permission gates under the boundary contract. Never/user-only restrictions remain prohibitions.

Implement the complete agreed outcome with the smallest coherent set of changes. Choose routine technical and procedural details independently within that scope. Preserve unrelated content and concurrent edits. Apply necessary corrections to your own work within the existing authorization; they do not require a separate audit or Fix invocation. Do not expand scope, substitute a different outcome, or drop requirements to finish faster.

## Resolve discoveries without restarting refinement

When a new substantive choice appears, explain the choice and its consequence and **prompt the user** through an assigned-choice Refine handoff. Pause the entire task, including independent work, until the answer arrives or explicit scoped permission allows the stated recommended answer to be assumed under the boundary contract. Do not treat a recommendation or silence alone as the user's decision.

Pass only the unresolved choice, baseline references, relevant evidence and owner constraints, and expected return. Retain the caller's continuation. Resume the task after an answer or authorized assumed resolution within current authority; material scope or permission changes need their own resolution. Retrieve facts yourself rather than turning routine investigation into user decisions.

## Verify and deliver

Check the actual result against every agreed requirement with proportionate evidence. Run meaningful behavioral tests when warranted; use direct inspection or artifact checks for simple changes. A successful file write alone is not verification. Correct in-scope failures and recheck the affected behavior. If verification is unavailable or blocked, report what was applied, what remains unverified, and its effect; do not claim full completion.

Return the result, changed artifacts, verification evidence, limitations, blockers, and unmet requirements concisely. Complete the task only when the agreed outcome is fulfilled and the required checks pass. An unanswered user question pauses the whole task; other pending handoffs keep their dependent outcomes pending.

Keep accepted choices in the existing topic record and maintain its one separate checkpoint when sustained work needs it, with actual applied/verified states from artifact owners. A short task can finish in chat without creating another specification, report format, or history. Context Refresh is optional authorized maintenance.

Implement does not take over the meaning or maintenance of specialized artifacts. Text files may be implementation artifacts; a separate synthesized document uses [To Document](../to-document/SKILL.md) when requested. [Smokes](../smokes/SKILL.md) is an optional requested audit; acting on its report belongs to [Fix](../fix/SKILL.md) when explicitly called. None is a mandatory stage of Refine → Implement. Publication, Git mutations, personal installation, and other actions remain subject to the requested task and current boundaries.
