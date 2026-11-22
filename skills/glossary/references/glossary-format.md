# Glossary Format

Use one glossary per coherent project or topic. Adapt the following structure to an existing compatible glossary.

```markdown
# Glossary: Community Workshop

Scope: Planning a recurring workshop for local residents.

## Agreed terms

### Participant
A person attending a workshop session to learn or contribute.
Avoid: customer, when referring to workshop attendance.

## Proposed terms

### Accessible session
A session that meets the participation needs identified for its intended audience.
Needs agreement: which needs and accommodations are included in this project.
```

## Entry rules

- Use the canonical term as the entry heading. For a proposed entry, the heading is the proposed canonical term.
- **Be opinionated.** Recommend one canonical term when multiple words refer to the same concept. Explain meaningful trade-offs without treating your recommendation as an agreed decision.
- **Keep definitions tight.** Define each term in one or two sentences within the stated scope. This limit applies to the definition, not optional examples, qualifiers, aliases, or sources.
- **Define what it IS, not what it does.** If a useful definition cannot satisfy this rule, explain why and ask the user to approve an exception before recording that definition.
- **Include terms that need contextual precision.** Add a term when its meaning, boundaries, or preferred wording matter to the project or topic. Exclude general vocabulary unless its meaning in this context needs clarification.
- Separate agreed terms from proposed terms. Move an entry into the agreed section only when the discussion establishes agreement. An unambiguous definition supplied by the user can establish agreement; an agent recommendation alone cannot.
- Use `Avoid:` only for alternative words that would introduce meaningful ambiguity or conflict with the agreed vocabulary. Do not prohibit legitimate distinctions or harmless everyday phrasing.
- Record accepted alternative names as aliases when useful. Do not list an accepted alias under `Avoid:`.
- Add an example, scope qualifier, or source only when it clarifies the definition.
- For proposed entries, state what remains unsettled: the term, its meaning, its scope, or its acceptance. Keep questions about actions, decisions, or implementation in the discussion record.
- Group entries under descriptive subheadings when natural clusters improve navigation. Otherwise, use a flat list within each agreement-status section. Do not create empty categories merely to match an example.
- If no terms require definition yet, retain the glossary's scope and note that no terms have been identified. Revisit this as the discussion develops.

Keep definitions independent of the chosen solution wherever possible. For example, define a participant by their role, not by the database table that stores them. A glossary is not a transcript, decision log, or specification.
