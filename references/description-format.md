# The description format

The default layout `/branch-pr` writes when the repository has no PR/MR template of its own.
Four sections, always in this order, always present.

## Overview

- 2-4 sentences. First the problem or goal (from the ticket or the commits), then what this
  change does about it, at the level of behaviour: "Refunds can now be partial", not
  "Changed refund.py".
- Then a line with the ticket references: `Closes #17 · Ticket: SHOP-42`. Use `Closes` only for
  tickets this branch is known to close (a closing keyword in a commit, or the user said so).
- If uncommitted work is included and looks unfinished, don't mention it here; mention it in Caveats.

## Changes

- 3-8 bullets. Each starts with a **bold area or behaviour**, then what changed and why it
  matters. Group small related edits into one bullet (for example "tests" or "renames").
- Name a key file in backticks at the end of a bullet when it helps a reviewer find the code.
  Never list every file: the PR already shows them.
- Order: user-visible behaviour first, then API/data changes, then internal refactors, then
  tests and docs.

## Caveats

Only what a reviewer, QA or the deployer needs to act on or keep in mind. Typical labels:

| Label | When |
|---|---|
| **Migration** | A schema or data migration: reversible? slow or locking on large tables? must run before the code? |
| **Config** | A new or changed env var, setting or feature flag: name, default, where it must be set |
| **Dependency** | A new or upgraded package |
| **Breaking change** | A removed/renamed public method, endpoint, field, event or file other code or clients use |
| **Deploy order** | Something must be deployed, migrated or backfilled first |
| **Not done** | A requirement from the ticket this branch does not implement, or only partly |
| **Limitation** | Known gaps, TODOs left in, behaviour deliberately out of scope |
| **Follow-up** | Work that should come in a later ticket |

No caveats → `- None.`

## QA test scenarios

- 4-8 checklist items: `- [ ] **Name**: steps → expected result`.
- Cover, in this order and only when they apply: the main success path, other valid variants,
  validation/invalid input, failure and error handling (external service down, timeout),
  boundary/edge cases (zero, max, empty, duplicate, concurrency), permissions, and one regression
  check of behaviour next to the change that must still work.
- Steps are short and concrete (endpoint, screen, input values); expected results are observable
  (status code, message, record state, email sent).

## Example

Title: `SHOP-42: Support partial refunds with amount validation`

````markdown
## Overview
Support agents could only refund an order in full, so a damaged item meant refunding everything
and re-charging the rest. This adds partial refunds: an agent refunds any amount up to the
remaining balance, and invalid amounts are rejected before anything is charged back.

Closes #17 · Ticket: SHOP-42

## Changes
- **Partial refunds**: `POST /orders/:id/refunds` refunds a given amount and reduces the order
  balance (`app/controllers/orders.py`)
- **Validation**: rejects zero, negative and over-balance amounts, and amounts above the
  configurable per-refund limit (`app/services/refund.py`)
- **Storage**: new `refunds` table records each refund (`db/migrate/20261123_add_refunds.py`)
- **Cleanup**: removed the unused `legacy_refund` helper; renamed `old_name.py` to `new_name.py`
- **Tests**: unit tests for the refund service

## Caveats
- **Migration**: adds the `refunds` table; run it before deploying the code.
- **Config**: `REFUND_MAX_CENTS` caps a single refund (default 100000 = $1,000); set it per
  environment if a different cap is needed.
- **Breaking change**: `legacy_refund` and the `index` action are removed; no callers remain in
  this repo.
- **Limitation**: the limit is global, not per merchant (TODO left in `refund.py`).

## QA test scenarios
- [ ] **Partial refund**: refund 20.00 on a 100.00 order → 201, balance 80.00, refund recorded
- [ ] **Full remaining balance**: refund exactly the balance → 201, balance 0.00
- [ ] **Invalid amount**: refund 0 or -5 → 422 "invalid amount", balance unchanged
- [ ] **Over balance**: refund 150.00 on a 100.00 order → 422, nothing refunded
- [ ] **Over limit**: refund above `REFUND_MAX_CENTS` → 422 "over limit"
- [ ] **Regression**: a full refund through the existing flow still works
````
