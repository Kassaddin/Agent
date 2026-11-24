# Remote Search

Use only configured sources with access.status ready or limited and sufficient effective read capability. A writable source can be read; technical write capability never authorizes mutations. Respect investigation, source, version-control, and actual connector permissions. Skip unavailable/unchecked sources with a coverage reason instead of asking to configure them during search.

Prefer a connected source's read-only search, file, or record API. Search only the configured repository or exact resource scope, not its entire host or account. A bounded query must not turn into unrestricted web search. Do not clone, fetch, pull, upload query data to an unlisted service, build an index, or test a write. Missing access produces a coverage limitation for the caller to handle.

For a repository, search filenames/tree metadata first for a locator question and content for a passage question. Use the requested revision when supplied; otherwise report the inspected branch or revision when available. The local checkout may contain uncommitted or newer material, while a vault or remote may be older. Preserve known source notes and return conflicting evidence rather than deciding which source wins.

Provider search may ignore case controls, index only a default branch, impose limits, or omit some file types. Apply a requested case-sensitive filter to retrieved evidence where possible and mark coverage partial when provider limits prevent verification. Do not claim a case-insensitive or regex search was exhaustive if the provider could not perform the requested semantics. Use bounded text extraction only when authorized and available; otherwise mark the format unsupported.

Return exact URLs or identifiers, excerpts, actual query terms, revision information when known, and coverage. Verify a result's line number against the source before returning it; use a section or record identifier instead when line numbers are not supported. On access failure, stop requests to that source, report the failure, and continue other permitted sources within the same budget only when no user question is pending. Do not hide a failed source behind no_matches.
