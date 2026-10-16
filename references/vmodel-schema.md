# `.vmodel/` schema

Project-local Single Source of Truth. Every A.I.D publish lives here so a fresh clone starts with history.

```text
.vmodel/
├── graph/
│   ├── meta.json          # { "graph_version": N, "projects": ["ACME"], "source_commit": "<sha or null>", "updated_at": "<iso>" }
│   └── edges.json         # [ { "from": "FNC-ACME-001", "to": "REQ-ACME-001", "type": "implements" }, ... ]
├── registries/
│   ├── usr.json           # { "USR-ACME-001": { ...node }, ... }
│   ├── req.json
│   ├── fnc.json
│   ├── api.json
│   ├── cmp.json
│   ├── int.json
│   ├── unt.json
│   ├── tst.json
│   ├── tol.json
│   ├── rsh.json
│   ├── std.json
│   ├── voc.json
│   ├── evd.json
│   └── scope.yaml         # project scope briefs used by the intake filter
├── proposals/             # writable by every role; ssot-gate alone moves them to processed/
│   └── processed/
├── baselines/             # one markdown file per publish: YYYY-MM-DD-gN.md
├── lint/
│   └── latest.json
└── docs/                  # rebuilt by /docs; safe to regenerate
    └── index.html
```

## Common node fields
Every registry entry is keyed by its id and carries at least:

| Field | Type | Notes |
|---|---|---|
| `id` | string | `{KIND}-{PROJECT}-NNN` |
| `kind` | string | Matches the registry |
| `project` | string | Must equal the PROJECT token in the id |
| `title` | string | Short label |
| `version` | integer | Starts at 1; bumped on every accepted amend |
| `status` | string | `proposed` \| `published` \| `amended` \| `retired`. For TST also: `not_run` \| `passed` \| `failed` \| `skipped` (only `EVD` may move a TST off `not_run`) |
| `statement` | string | The checkable text |
| `created_at` / `updated_at` | ISO-8601 | |
| `proposed_by` | string | Subagent name |

Kind-specific extras (all optional unless noted):
- **USR:** `who`, `why`, `constraints[]`, `source`
- **REQ:** `priority` (`must`/`should`/`could`), `acceptance` (required, measurable), `type` (`functional`/`constraint`/`quality`)
- **FNC:** `inputs[]`, `outputs[]`, `rule`
- **API:** `route` or `channel`, `contract_version`, `request` `{headers,query,body}`, `response.success.body`, `errors[]`
- **CMP:** `responsibilities[]`
- **INT:** `from_cmp`, `to_cmp`, `carries_api`, `implements_fnc`
- **UNT:** `fields[]` `{name,type,meaning,set_by,read_by}`, `inputs[]`, `returns`, `rules[]`, `algorithms[]`, `source_files[]`
- **TST:** `level` (required), `cases[]` `{input,expected}`, `verifies` is carried as edges
- **EVD:** `command`, `commit`, `ran_at`, `outcome`, `artifact_path`
- **RSH:** `question`, `answer`, `sources[]`, `asked_by`
- **TOL:** `tool`, `version`, `purpose`
- **STD / VOC:** `rule` or `term` + `definition`

## Proposal shape
```json
{
  "action": "create" | "amend" | "retire",
  "kind": "REQ",
  "id": "REQ-ACME-001",
  "proposed_by": "req-guardian",
  "base_version": 1,
  "previous": { "...exact live node..." },
  "new_full": { "...complete new node..." },
  "edges_add": [ { "from": "...", "to": "...", "type": "derives" } ],
  "edges_remove": []
}
```
For `create`, omit `previous` and set `base_version` to `0`. For `retire`, `new_full.status` is `retired`.

## Edge types
`derives` (REQ→USR), `implements` (FNC|API→REQ), `allocated_to` (FNC→CMP), `integrates_with` (INT→CMP), `depends_on`, `refines` (UNT→FNC|CMP), `verifies` (TST→REQ|FNC|UNT|API|INT|CMP), `supersedes`, `evidences` (EVD→TST). Both ends of an edge must share the same `project`.

## Empty bootstrap
`/setup-aid` creates empty registries (`{}`), `edges.json` as `[]`, and `meta.json` with `graph_version: 0`.


## Code traceability
Source that implements a published `UNT` carries a machine tag and nothing else as a comment:

- Form: `@trace UNT-{PROJECT}-NNN` inside the language's comment syntax.
- Place one tag on each function or module that implements the unit. A unit may span several functions; each carries the same UNT id.
- Only the UNT id appears in the tag. REQ / FNC / CMP lineage is read from the graph (`UNT refines CMP|FNC`, `FNC implements REQ`).
- Tags name only published UNT ids. Adept never mints ids.
- No explanatory human comments; names and small functions explain the logic.
- Lint: `python3 <plugin>/scripts/vmodel_lint.py .vmodel --code <src-dir>` reports orphan tags, untagged published units and malformed tags under a **code trace** heading (or "no trace flags").
