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
    ├── index.html
    └── v-view.html        # interactive V debug view (ssot-gate / /v-view)
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
- **USR:** `who`, `why`, `constraints[]`, `source`, `effort` `{lane, gates, use, done_enough, futures[], stages[], reason, grow_for}` (`tiny` 2 / `small` 4 / `standard` 7 / `large` 11; required on create — Imagine the use)
- **REQ:** `priority` (`must`/`should`/`could`), `acceptance` (required, measurable), `type` (`functional`/`constraint`/`quality`), `effort` (copy from the parent USR unless this REQ earns a different lane with a written reason)
- **FNC:** `inputs[]`, `outputs[]`, `rule`
- **API:** `route` or `channel`, `contract_version`, `request` `{headers,query,body}`, `response.success.body`, `errors[]`
- **CMP:** `responsibilities[]`
- **INT:** `from_cmp`, `to_cmp`, `carries_api`, `implements_fnc`
- **UNT:** `fields[]` `{name,type,meaning,set_by,read_by}`, `inputs[]`, `returns`, `rules[]`, `algorithms[]`, `source_files[]`. Optional `ui` when the unit is a user-facing screen, page, dialog or visible control: `layout`, `visual_hierarchy`, `spacing`, `type_scale`, `colour`, `contrast` (WCAG AA), `states[]` (must include empty, loading, error, hover, focus, disabled), `keyboard`, `accessibility`, `breakpoints[]`. Adept designs this (`ui-design` skill) before coding; unit-designer records it here, or Adept writes `.vmodel/docs/<PROJECT>/ui/<UNT-id>.md`. Code must follow the record.
- **TST:** `level` (required), `cases[]` `{input,expected}`, `verifies` is carried as edges
- **EVD:** `command`, `commit`, `ran_at`, `outcome`, `artifact_path`
- **RSH:** `question`, `answer`, `sources[]`, `asked_by`
- **TOL:** `slot` (required: `language` \| `framework` \| `package_manager` \| `test_runner` \| `linter` \| `deploy_target` \| `library` \| `api`), `tool` (required; the chosen name, or `none`), `tool_version` (semver, exact, or `unspecified`; do not overload the node integer `version`), `purpose`, `evidence[]` (repo files that justified detection; empty if the user stated the slot), `confirmed` (required boolean; `true` only after the user accepted the stack), `comment_syntax` (language slot: how source comments are written, e.g. `#`, `//`, `/* */`, `--`, `<!-- -->`), `command` (test_runner / package_manager / linter invocation), optional `api_id` (`library`/`api` slots: published `API` id). One live TOL per exclusive slot (`language`…`deploy_target`) per project; many `library`/`api` allowed. `tools-manager` is the only author.
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
  "edges_remove": [],
  "decision": {
    "question": "one line",
    "options": ["a", "b", "c"],
    "chosen": "a",
    "reason": "why this is most likely correct",
    "rejected": [{ "id": "b", "why": "..." }],
    "predicted": "what should be true if the pick is right",
    "check": "observable later",
    "effort": {
      "use": "who, where, how long, how often",
      "done_enough": "from the user's side",
      "futures": ["smallest honest", "..."],
      "lane": "tiny",
      "gates": 2,
      "stages": ["USR", "REQ"],
      "reason": "why this lane matches the use",
      "grow_for": null
    }
  }
}
```
For `create`, omit `previous` and set `base_version` to `0`. For `retire`, `new_full.status` is `retired`. `decision` is required on a create/amend that is a design or mint choice (`aid-curiosity-imagination`). The gate copies it into the baseline **Decisions** section. It is notes, not a registry kind.

## Edge types
`derives` (REQ→USR), `implements` (FNC|API→REQ), `allocated_to` (FNC→CMP), `integrates_with` (INT→CMP), `depends_on`, `refines` (UNT→FNC|CMP), `verifies` (TST→REQ|FNC|UNT|API|INT|CMP), `uses` (UNT|TST→TOL), `supersedes`, `evidences` (EVD→TST). Both ends of an edge must share the same `project`. `uses` is optional catalog linkage (a unit or test names the tool it depends on); TOL nodes are valid with no incoming edges.

## Empty bootstrap
`/setup-aid` creates empty registries (`{}`), `edges.json` as `[]`, and `meta.json` with `graph_version: 0`.


## Code traceability
Source that implements a published `UNT`, and tests that implement a published `TST`, carry a machine tag and nothing else as a comment:

- Form: `@trace UNT-{PROJECT}-NNN` on product functions/modules, `@trace TST-{PROJECT}-NNN` on test functions, inside the **confirmed language TOL** `comment_syntax` (never guessed).
- Place one UNT tag on each function or module that implements the unit. A unit may span several functions; each carries the same UNT id.
- Place one TST tag on each test that implements a planned TST.
- Only that one id appears in the tag. REQ / FNC / CMP lineage is read from the graph (`UNT refines CMP|FNC`, `FNC implements REQ`, `TST verifies …`).
- Tags name only published UNT or TST ids. Adept never mints ids.
- No explanatory human comments; names and small functions explain the logic.
- Lint: `python3 <plugin>/scripts/vmodel_lint.py .vmodel --code <project-tree>` reports orphan tags, untagged published units, a planned TST with no test in code carrying that id, malformed tags, and a project that has source or UNT records but no published TOL, under a **code trace** heading (or "no trace flags"). Pass `--code` a tree that includes both product source and tests.

## Stack (TOL)
A project that has product code (published `UNT`, or source files in a `--code` scan) must have at least one published `TOL`. `/setup-aid` runs `stack-detect`, the user confirms, `tools-manager` proposes, `ssot-gate` publishes. Adept, Test Master and `/usr` refuse to write code or tests until `confirmed: true` language and test_runner slots exist. Never assume a stack when the repo is empty or unclear.
