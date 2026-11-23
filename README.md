# claude-code-branch-pr: PR / MR descriptions for your branch with Claude Code

**`/branch-pr` is a skill and plugin for [Claude Code](https://claude.com/claude-code)** that writes the pull request (GitHub, Bitbucket, Azure DevOps) or merge request (GitLab) description for the **current git branch**. Type `/branch-pr`, optionally paste the ticket on the next lines, and you get a brief, copy-paste-ready Markdown description:

- **Overview**: the problem and what this change does about it, with the ticket reference.
- **Changes**: what changed, grouped by behaviour, not a file dump.
- **Caveats**: migrations, new env vars and feature flags, new dependencies, breaking changes, deploy order, TODOs left in, and requirements that are **not done**.
- **QA test scenarios**: a short checklist covering the success path, validation, failures, edge cases and one regression check.

Plus a [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary) title with the type and the affected area: `feat(refunds): support partial refunds with amount validation`, `fix(auth)!: reject expired tokens on refresh`. The description is saved to `.branch-pr/PR_DESCRIPTION.md`, **copied to your clipboard**, and shown raw in the chat.

## Usage

```text
/branch-pr
/branch-pr SHOP-42
/branch-pr https://tracker.example.com/browse/SHOP-42
/branch-pr docs/tickets/shop-42.md --base develop
/branch-pr
As a support agent I can refund part of an order.
- Amount must be > 0 and <= remaining balance
- Refunds above the configured limit are rejected
```

| Option | Meaning |
|---|---|
| `--base <branch>` | Base branch (default: auto-detected main / master / develop / origin's HEAD) |
| `--committed-only` | Leave uncommitted and untracked work out |
| `--template <file>` / `--no-template` | Fill this template / ignore the repo's own |
| `--platform github\|gitlab\|bitbucket\|azure` | Override the host detected from `origin` |
| `--no-copy` | Don't copy to the clipboard |
| `--draft` | The suggested create command opens a draft |
| `--create` | Open the PR/MR with `gh` / `glab` after you confirm |
| `-- <text>` | Extra instructions ("mention the rollout plan", "shorter") |

## How it works

1. **`collect.py`** diffs the branch against its merge-base with the base branch (uncommitted and untracked work included), and writes `.branch-pr/context.json` and `diff.patch`:
   - commits, and ticket ids from the branch name and commit messages (`closes #17` is noticed);
   - each changed file's kind (source, test, migration, schema, dependency, config, infra, CI, docs, ...), +/- lines and its offset in the patch, so a big diff can be read in parts;
   - **caveat signals**: migrations, dependency changes, env vars read by new code, feature flags, routes and GraphQL fields, removed public definitions, deleted tests, TODOs, debug output and secret-looking values;
   - the repo's own PR/MR template (`.github/pull_request_template.md`, `.gitlab/merge_request_templates/*.md`, ...);
   - the hosting platform, from `origin`;
   - **title hints**: a suggested Conventional Commits type (from conventional commit messages already on the branch, or from the file kinds) and scope candidates from the changed areas.
2. **Claude reads** the requirements, the commits and the diff, and checks each signal against the code. Only the real ones become caveats. Each requirement is mapped to done / partly done / not done.
3. It writes the title and description, filling the repo's template when there is one.
4. **`finalize.py`** checks the result: a valid Conventional Commits title (known type, scope, `!` matching a breaking-change caveat), all sections present, QA scenarios listed, under the platform's size limit, no secret-looking values, no leftover placeholders or local paths. Then it copies the description to the clipboard and prints the `gh pr create` / `glab mr create` command.

Nothing in your repo changes except `.branch-pr/`, which is git-ignored automatically. Nothing is pushed or opened unless you pass `--create` and confirm. The scripts use only the Python 3 standard library.

## Install

**As a plugin:**

```text
/plugin marketplace add rewin0087/claude-code-branch-pr
/plugin install branch-pr@rewin0087
```

**As a personal skill:**

```bash
git clone https://github.com/rewin0087/claude-code-branch-pr ~/.claude/skills/branch-pr
```

## Example output

See [references/description-format.md](references/description-format.md) for the format rules and a full example.

## Related skills

- [`/branch-review`](https://github.com/rewin0087/claude-code-review): AI code review of your branch.
- [`/branch-qa`](https://github.com/rewin0087/claude-code-branch-qa): headless E2E and functional QA of your branch against its ticket.
- [`/investigate`](https://github.com/rewin0087/claude-code-investigate): trace a flow and reproduce bugs.

## License

MIT
