# Issue tracker: Local Markdown

Issues and specs for this project live as Markdown files in `.scratch\`.

## Conventions

- One feature per directory: `.scratch\<feature-slug>\`.
- The spec is `.scratch\<feature-slug>\spec.md`.
- Implementation issues are separate files at `.scratch\<feature-slug>\issues\<NN>-<slug>.md`, numbered from `01`; never combine tickets into one file.
- Record issue state in a `Status:` line near the top of each issue.
- Append comments and conversation history under a `## Comments` heading.

## When a skill says "publish to the issue tracker"

Create a file under `.scratch\<feature-slug>\`, creating the directory if needed.

## When a skill says "fetch the relevant ticket"

Read the referenced local file. If only a ticket number is supplied, resolve it within the relevant feature directory.

## Wayfinding operations

Used by `/wayfinder` if installed. The map has one child file per ticket.

- Map: `.scratch\<effort>\map.md`, containing Notes, Decisions-so-far, and Fog.
- Child ticket: `.scratch\<effort>\issues\NN-<slug>.md`, numbered from `01`, with the question in its body. A `Type:` line records `research`, `prototype`, `grilling`, or `task`; a `Status:` line records `claimed` or `resolved` once work starts.
- Blocking: a `Blocked by: NN, NN` line lists dependencies. A ticket is unblocked when every listed ticket is resolved.
- Frontier: scan child tickets for open, unblocked, unclaimed work; the lowest number wins.
- Claim: set `Status: claimed` and save before starting work.
- Resolve: append the answer under `## Answer`, set `Status: resolved`, then append a summary and child-ticket link to Decisions-so-far in the map.
