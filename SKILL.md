---
name: branch-pr
description: Write a pull request / merge request description for the current git branch. Reads the branch's diff and commits (uncommitted work included), the requirements (ticket text, file, URL or what the user wrote) and the repo's own PR/MR template, then writes a brief, copy-paste-ready Markdown description with an overview, the list of changes, caveats (migrations, env vars, breaking changes, unmet requirements) and short QA test scenarios, plus a title. Saves it to .branch-pr/PR_DESCRIPTION.md, copies it to the clipboard, and prints the raw Markdown in the chat.
argument-hint: "[requirements text on the next lines | ABC-123 | #123 | ticket URL | ticket file] [--base <branch>] [--committed-only] [--template <file> | --no-template] [--platform github|gitlab] [--no-copy] [--draft] [--create] [-- instructions]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/collect.py *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/finalize.py *) Bash(git diff *) Bash(git log *) Bash(git show *) Bash(git status *) Bash(git grep *) Bash(git rev-parse *) Bash(git ls-files *) Bash(ls *) Read Grep Glob WebFetch Write(**/.branch-pr/**) Edit(**/.branch-pr/**)
---

# Pull request / merge request description for the current branch

Arguments: `$ARGUMENTS`

You write the description a careful senior engineer would write for their own branch: short,
specific and true to the diff. A reviewer should understand **why** the change exists, **what**
changed, **what could bite** them, and **how to check it** in under a minute of reading.

## Arguments

- **Requirements** (what the branch is supposed to implement), from any of:
  - the text the user typed after `/branch-pr`, on the same line or the lines below it
    (acceptance criteria, a pasted ticket, a todo list, "it must…" sentences);
  - a ticket file (`.md`, `.txt`, `.pdf`, `.docx`, an image of the ticket or mockup): read it;
  - a URL: fetch it with WebFetch. If it needs a login and fails, say so in one line and continue
    without it; never ask for credentials;
  - a bare ticket id (`ABC-123`, `#123`): use it as the ticket reference. Do not try to fetch it
    from a tracker unless the user also gave a URL;
  - files or images attached or `@`-mentioned in the conversation that are not code.
  No requirements given → infer the intent from the commits and the diff, and do not invent
  acceptance criteria.
- `--base <branch>` (or a bare word that is an existing branch name) = the base branch. Default:
  auto-detected (the closest of origin's HEAD, main, master, develop, ...).
- `--committed-only` = describe committed work only (default: uncommitted and untracked work is
  included, because it usually ends up in the PR).
- `--template <file>` = fill this template. `--no-template` = ignore the repo's template.
- `--platform github|gitlab|bitbucket|azure` = override the host detected from `origin`.
- `--no-copy` = don't copy to the clipboard. `--draft` = the suggested create command opens a draft.
- `--create` = also open the PR/MR with `gh` / `glab` after the user confirms (Step 6).
- everything after ` -- ` = extra instructions (tone, things to mention or leave out).

## Step 1: Collect the branch

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/collect.py [--base <b>] [--committed-only] [--template <f> | --no-template] [--platform <p>]
```

Run it from the repo (or pass `--repo <dir>`). If the current directory is not a git repo, look
one level down for repos (`ls -d */.git`) and use the only one, or ask which. If it reports
**no changes**, tell the user and stop.

It prints a digest and writes into `.branch-pr/` (kept out of git automatically):
- `context.json`: branch, base, commits (subject and body), ticket ids found in the branch name
  and commits, every changed file with its kind (source, test, migration, schema, dependency,
  config, infra, ci, style, docs, asset, noise), +/- lines and its start line in `diff.patch`,
  the **caveat signals**, the repo's PR/MR template, and the hosting platform.
- `diff.patch`: the whole branch diff, source first, lockfiles and build output left out.

## Step 2: Understand the change

1. Read the requirements (see Arguments) and the commit messages: they tell you the intent.
2. Read `diff.patch`. For a big diff, read it in parts with `Read` and the `diff_line` offsets
   from the digest, in this order: source, migration/schema, config/dependency, then tests.
   Skim tests for **what behaviour they assert**, which is a good source for QA scenarios.
3. When a hunk is unclear without its surroundings, read the file itself or `git grep` for its
   callers. Spend effort on understanding, not on reviewing: this is not a code review, so don't
   list style nits or bugs, unless a bug is serious enough to be a caveat.
4. **Check every caveat signal** against the code. Keep it only if it is real and matters to a
   reviewer or deployer: a renamed method with no other callers is not a breaking change; an
   env var read with a safe default is a note, not a blocker; a `print` in a CLI is not debug output.
5. If requirements were given, map each one to the change: **done**, **partly done** or
   **not done**. Anything not done or only partly done becomes a caveat. Do not claim something
   is done that the diff does not show.

## Step 3: Write the title and description

Write two files with the Write tool (paths are in the digest):
- `.branch-pr/PR_TITLE.txt`: one line, imperative mood, under 72 characters, with the ticket id
  first when there is one: `SHOP-42: Support partial refunds with amount validation`.
- `.branch-pr/PR_DESCRIPTION.md`: the description, in the format below.

**If the repo has a PR/MR template** (`template` in the digest), keep its headings, order and
checkboxes and fill each section with the matching content below. Put anything that has no home
in the template (usually Caveats or QA) under a new heading at the end. Remove its instructional
`<!-- comments -->` once a section is filled. Tick a template checkbox only when the diff proves
it (for example "tests added" when test files changed); leave the rest unticked.

**Otherwise** use this layout (full rules and an example in
[references/description-format.md](references/description-format.md)):

```markdown
## Overview
<2-4 sentences: the problem or goal, then what this change does about it. Link the ticket.>

Closes #17 · Ticket: SHOP-42

## Changes
- **<Area or behaviour>**: <what changed and why it matters, not a file list> (`path/key_file.py`)
- ...

## Caveats
- **<Migration / Config / Breaking change / Deploy order / Not done / Follow-up>**: <what, and what to do about it>

## QA test scenarios
- [ ] **<Scenario>**: <short steps> → <expected result>
- ...
```

Rules that matter most:
- **Brief.** About 150-400 words for a typical branch. The Overview is a paragraph, not an essay.
  Changes: 3-8 bullets, grouped by behaviour or area, merging small related edits; mention a key
  file in backticks only where it helps the reviewer find the code. QA: 4-8 scenarios.
- **True to the diff.** Every claim must be visible in the diff, the commits or the requirements.
  No speculation about impact you didn't check, and no marketing words.
- **Caveats** cover what a reviewer, QA or the deployer must know: migrations (reversible? slow
  on big tables? run order), new or changed env vars/config/feature flags, new dependencies,
  breaking API/contract changes, deployment order, data backfills, known limitations, TODOs left
  in, requirements not done, and follow-ups. If there are none, write `- None.`
- **QA test scenarios** are short and runnable by someone else: the main success path first,
  then validation/invalid input, failure/error handling, edge or boundary cases, permissions if
  relevant, and one regression check on behaviour next to the change. Use checklist items
  (`- [ ]`). Tie them to the acceptance criteria when there are any.
- Readable as **raw Markdown** and rendered: plain headings, lists, inline code; no HTML, no
  tables unless a comparison truly needs one, no emoji.
- **Never include** secrets, tokens, real customer data, internal hostnames from config, absolute
  local paths (`/Users/...`), or the `.branch-pr/` folder. Refer to people by role.
- Use the platform's words: "pull request" on GitHub/Bitbucket/Azure, "merge request" on GitLab.
  `Closes #N` / `Closes ABC-123` only for tickets the commits or the user say this branch closes;
  otherwise list them as `Ticket:` / `Related:`.
- Follow any instructions after ` -- `.

## Step 4: Check it

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/finalize.py --copy [--draft]
```

(`--no-copy` from the user → drop `--copy`.) It checks the sections, the QA list, the size limit
of the platform, secret-looking values, leftover placeholders and local paths, then copies the
description to the clipboard. On **FAIL**, fix the files and run it again. Fix warnings too
unless they are deliberate (say which ones you kept and why).

## Step 5: Show it in the chat

Reply with, in this order:
1. One line: the branch, base and size (`feature/x ← main · 7 files, +120/-30`), and whether
   uncommitted work is included.
2. **Title** in a one-line code block.
3. **Description** as raw Markdown inside a fence of **four** backticks with the `markdown`
   language, so the user can copy it exactly, including any inner code blocks:
   `````text
   ````markdown
   ## Overview
   ...
   ````
   `````
4. One line saying it was copied to the clipboard (or not, and why), with the file path of
   `PR_DESCRIPTION.md`.
5. If there were requirements: a short list of any requirement that is **not done** or only
   **partly done**. If the caveat signals turned up something worth a second look before
   merging (a secret-looking value, debug output, a removed method still in use), say so in one
   line each. Don't repeat the description itself.
6. The create command from the digest (`gh pr create ...` / `glab mr create ...`) for the user to
   run, if the platform has one.

## Step 6: Create the PR/MR (only with `--create`)

Opening a PR/MR is visible to the team, so do it only when the user passed `--create` (or asks for
it afterwards), and **confirm first** with AskUserQuestion, showing the title, base and head.
The branch must be pushed: if `git status` shows it has no upstream or is ahead of it, say so and
ask before pushing. Then run the create command printed by `finalize.py` and give the user the
URL it returns. If `gh`/`glab` is missing or not logged in, say so and stop: the copied
description is enough for the user to paste.

## Notes

- Nothing in the repo is changed apart from `.branch-pr/`; no code is edited, nothing is pushed
  or created without `--create` and the user's confirmation.
- Run again after more commits: it re-collects and rewrites the description from scratch.
  If the user edited `PR_DESCRIPTION.md` by hand and asks for an update, read their version
  first and keep their edits.
