# Domain Docs

How engineering skills should consume this project's domain documentation.

## Before exploring, read these

- Root `GLOSSARY.md` for domain terminology.
- ADRs in `docs\adr\` that touch the area being explored.

If these files do not exist, continue without flagging their absence or suggesting that they be created upfront. Create glossary entries and ADRs lazily when terms or decisions are actually resolved.

## File structure

This project uses a single-context layout: one root `GLOSSARY.md` and one `docs\adr\` directory. ADR filenames use a numeric prefix and descriptive slug, such as `docs\adr\0001-example-decision.md`.

## Use the glossary's vocabulary

When naming a domain concept in an issue, refactor proposal, hypothesis, or test, use its defined glossary term. Do not substitute synonyms the glossary explicitly avoids.

If a needed concept is missing, reconsider whether it belongs to this project's domain. Record genuine terminology gaps when domain modeling is next performed.

## Flag ADR conflicts

If a proposed change contradicts an existing ADR, surface the conflict explicitly rather than silently overriding it. Identify the ADR and explain why the decision may need reopening.
