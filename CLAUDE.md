# Workflow

- Commits are fine to create in this repo without asking each time.
- Never push to GitHub (`git push`) without explicit approval — the user wants to review the commit message before anything reaches the remote.
- After each response, append an entry to `docs/project_log.md` with an approximate token estimate (see that file's methodology section) and its category (code / image / discussion). This is a rough estimate, not an exact tokenizer count.
- Each entry gets a timestamp. Get the real current time via `date "+%Y-%m-%d %H:%M"` (Bash) rather than guessing or relying on the session's start-of-conversation date.
- Squash consecutive small entries (quick replies, single small edits, a commit) into one row rather than logging every turn separately — the log should highlight the larger chunks of work, not every message.
- Leave `project_log.md` itself uncommitted between real commits; fold its updates into the next substantive commit instead of committing it alone each time.
