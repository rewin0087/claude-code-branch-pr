# Changelog

## 1.1.0

- Titles follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary): `<type>(<scope>)[!]: <description>`.
- `collect.py` suggests a type and scope candidates; `finalize.py` rejects titles that don't follow the format and warns when `!` and the breaking-change caveat disagree.
- Scripts reorganised into the `core`, `branch`, `hosting`, `signals`, `title`, `description`, `collect` and `finalize` packages, one class per file; output is unchanged.
- The plugin marketplace is named `rewin0087-branch-pr` (install with `branch-pr@rewin0087-branch-pr`), so it doesn't clash with the other rewin0087 plugins.
- GitHub Pages site in `docs/`.

## 1.0.0

- `/branch-pr`: writes a PR/MR title and Markdown description for the current branch (overview, changes, caveats, QA test scenarios) from its diff, commits and the requirements given inline, as a file, URL or ticket id.
- `collect.py`: branch diff vs the auto-detected base (uncommitted and untracked work included), commits, ticket ids from the branch name and commits, files by kind with +/- lines and offsets into `diff.patch`, caveat signals (migrations, dependencies, env vars, feature flags, routes, removed definitions, deleted tests, TODOs, debug output, secret-looking values), the repo's PR/MR template, and the hosting platform.
- `finalize.py`: checks sections, the QA list, the platform's size limit, secrets, placeholders and local paths; copies to the clipboard; prints the `gh` / `glab` create command.
