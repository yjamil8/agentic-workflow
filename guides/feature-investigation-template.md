# Investigation: <feature name>

- Plan version: v1
- Updated: YYYY-MM-DD
- Status: <draft | in review | approved for vN | changes requested (PR-001)>
- Agent Table: agent_tables/<feature-slug>/TABLE.md (table ID <uuid>)
- Source: implementation_plans/MMDDYY/<feature-slug>/investigation.md
- Inspected source: <repo>@<40-character SHA> per repository inspected

## Revision history

- `v1`, YYYY-MM-DD: Initial investigation.

## Question

<What feature or problem this investigates, what the owner wants to know, and
what is explicitly outside the investigation.>

## Method

<Repositories and commits inspected, and every search run, with its count.>

```bash
rg -n "<symbol or string>" <paths>     # <count> matches
```

Blind spots checked: <reflection or string dispatch, configuration files,
scheduled jobs, pipelines and GitHub Actions workflows, other repositories,
generated code>.

## Inventory

### Entry points and call sites

| Location (file + symbol) | What it does today | Affected by the feature? Why |
|---|---|---|
| `<path>` `<Symbol>` | <behavior> | <yes / no, with the reason> |

### Data: readers and writers

| Store (table, container, blob path, queue) | Readers | Writers | Notes |
|---|---|---|---|
| <name> | <components> | <components> | <shape, volume in QA> |

### Contracts

<APIs, events, message schemas, file formats, and every consumer of each,
including deployed versions and cached clients that will keep using the old
shape.>

### Configuration and feature flags

<Settings, flags, and secrets involved, and where each is defined per
environment.>

### Third-party services

<Each service touched, how it is called, credentials location (never the
value), and whether a sandbox or test account exists.>

### User-facing surfaces

<Screens, messages, emails, exports, or reports a user would see change.
Write "None" if there are none.>

## Data shape (QA, read-only)

<Dated counts and shapes from the QA database, labeled as QA. What they show,
and what they cannot tell you about production.>

## Existing mechanisms that could be reused

<Services, components, patterns, or infrastructure already present that
could meet part of the need, with where they live.>

## Invariants and constraints

<Rules the code, data, or contracts enforce today that a change must
preserve, each traced to where it is enforced.>

## Unknowns

- <Question, why it matters, and how to resolve it. For anything only
  production data can answer: who can check it and the exact read-only query
  to give them.>

## Completeness

<How you know the inventory is complete: the searches above, the blind spots
checked, and anything you could not inspect and why.>
