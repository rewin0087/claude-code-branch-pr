# Changelog

## 1.0.0

- `/branch-pr`: writes a PR/MR title and Markdown description for the current branch (overview, changes, caveats, QA test scenarios) from its diff, commits and the requirements given inline, as a file, URL or ticket id.
- `collect.py`: branch diff vs the auto-detected base (uncommitted and untracked work included), commits, ticket ids from the branch name and commits, files by kind with +/- lines and offsets into `diff.patch`, caveat signals (migrations, dependencies, env vars, feature flags, routes, removed definitions, deleted tests, TODOs, debug output, secret-looking values), the repo's PR/MR template, and the hosting platform.
- `finalize.py`: checks sections, the QA list, the platform's size limit, secrets, placeholders and local paths; copies to the clipboard; prints the `gh` / `glab` create command.
