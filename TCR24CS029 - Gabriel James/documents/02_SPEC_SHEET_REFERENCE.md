# 02 Specification sheet reference

A specification sheet is the formal model of one unit of software: an application module, an
example application assembled from several modules, or a client requirement. Every sheet is an
instance of the same JSON Schema, `specs/capability.schema.json`, and can be written as
canonical JSON (`spec.json`) or YAML (`spec.yaml`). The two forms decode to the same model; the
CLI subcommand `spec-yaml` generates the YAML form from the JSON form and proves the round trip
by reloading it and comparing the decoded model.

This document names every field, its type, its default and the rule the parser applies. The
schema is normative; this text explains it.

## 1. Sheet kinds

| Kind | Location | Convention |
| --- | --- | --- |
| Module sheet | `modules/<module>/spec.json` | one sheet per Flask module, served by the module at `/spec` |
| Application sheet | `specs/app/*.yaml` | an example application: several capabilities, often from different modules, one domain |
| Requirement sheet | `specs/app/requirements/*.yaml` | an application sheet that declares exactly one capability: what the client asks for |

All three carry the same formal application model

    A = (S, C, S_I, G, R, K)

state variable schema `S`, capability set `C`, initial state `S_I`, goal specification `G`,
resources `R` and global constraints `K`. A requirement sheet is distinguished only by having
one capability in `C`; the resolver ranks it against the capabilities of the pool sheets.

## 2. Root fields

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `spec_version` | string, pattern `^[0-9]+\.[0-9]+$` | yes | format version of the sheet, currently `1.0` |
| `module` | object | yes | identity and deployment facts of the unit |
| `state_schema` | array, at least one entry | yes | `S`: the typed state variables |
| `initial_state` | object, at least one property | yes | `S_I`: the condition before execution |
| `resources` | array | yes | `R`: resources the unit can provide or consume |
| `constraints` | array | yes | `K`: global constraints and policies |
| `goal` | array of conditions, at least one | yes | `G`: the goal of the unit in isolation |
| `capabilities` | array, at least one entry | yes | `C`: the capability set |

Unknown root fields are rejected (`additionalProperties: false`): a typo becomes a validation
error instead of a silently ignored first-class fact.

### 2.1 `module`

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `module_id` | string | yes | stable identifier, for example `patient-registry` |
| `version` | string | yes | module version |
| `domain` | enum: `hospital`, `ecommerce`, `documents`, `generic` | yes | domain the module serves |
| `port` | integer 1..65535 | yes | TCP port of the module process |
| `base_url` | string | yes | origin the mechanism endpoints resolve against, for example `http://127.0.0.1:5001` |
| `health` | string | yes | health endpoint path relative to `base_url` |
| `description` | string | no | one line about the module |
| `language` | string | no | implementation language, `Python` for the Flask modules |
| `database_file` | string | no | SQLite file relative to the module root, when the module owns one |
| `ui` | string | no | UI root path served by the module, when it serves one |

The gateway discovers modules over HTTP at `base_url + health` and `base_url + /spec`; the port
convention of the project is 5001 to 5007 for the seven shipped modules.

### 2.2 `state_schema` entries

Each entry declares one state variable `x`.

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `name` | string, pattern `^[A-Za-z_][A-Za-z0-9_.]*$` | yes | dotted name, for example `Patient.registered` |
| `type` | enum: `boolean`, `integer`, `real`, `categorical`, `enumerated`, `structured` | yes | value type |
| `domain` | array or `"unbounded"` | yes | allowed values or range |
| `unit` | string | no | unit of a numeric variable |
| `kind` | enum: `value`, `counter`, `flag`, `status`, `resource` | no | role of the variable in the model |

Domain conventions:

- `boolean`: `[false, true]`.
- `enumerated`, `categorical`: the list of allowed values, for example `[ORDERED, RECEIVED, RESULTED]`.
- `integer`, `real`: either a two element `[min, max]` range or the string `"unbounded"`.
- `structured`: the list of component field names.

Two numeric domain entries are not read as a range by accident: the parser treats an array of
exactly two numbers as the range of a numeric variable only when the declared type is numeric.

The shared hospital and e-commerce vocabulary lives in `specs/state_variables.json`; module
sheets spell the variables out and the corpus test verifies that module, application and
requirement sheets agree on names and types.

### 2.3 `initial_state`

An object mapping declared state variable names to typed literals: `{"Lab.ordered": false}`.
Keys must appear in `state_schema`; the parser rejects an initial state over an undeclared
variable. The initial state is what the compatibility engine starts from when it seeds the
abstract domain for variables an effect set actually touches.

### 2.4 `resources` entries

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | resource identifier, referenced by a capability's `resources` list |
| `kind` | enum: `database`, `authentication_token`, `payment_gateway`, `network`, `file_system`, `gpu`, `external_service`, `clock` | yes | resource class |
| `available` | boolean | no, default true | whether the resource is present in this environment |
| `details` | string | no | human readable note |

The compatibility engine's resource check fails when a capability requires a resource whose
`available` is false, which is how a missing resource is simulated without touching the code.

### 2.5 `constraints` entries

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | identifier, for example `K-PATIENT-ID-FORMAT` |
| `kind` | enum: `input`, `state`, `resource`, `security`, `temporal`, `dependency`, `domain` | yes | constraint class |
| `expression` | string | yes | the constraint over typed state variables |
| `enforced_by` | string | no | endpoint or service function that enforces it |

Global constraints are documentation with a class: they are rendered in reports and validated
for presence, while executable checking happens through capability constraints and the
compatibility engine's operational checks.

### 2.6 `goal`

A list of typed conditions in the same form as preconditions (section 3.4). The goal of a
module sheet is its own objective in isolation; the goal of a requirement sheet is the client's
objective, and the goal encoder embeds it as the requirement vector.

## 3. Capabilities

Each capability is the formal tuple

    c = (T, I, O, P, E, K_i, R_i, Q, Rel, A, M)

with `T` the mechanism type, `I` and `O` the typed inputs and outputs, `P` the preconditions,
`E` the effects, `K_i` capability constraints, `R_i` required resources, `Q` quality attributes,
`Rel` reliability, `A` availability and `M` the execution mechanism.

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | stable identifier, for example `PR-Register` |
| `name` | string | yes | machine name, for example `register_patient` or `Pat_reg` |
| `type` | one of the nine capability types | yes | `T`: the delivery mechanism class (section 3.7) |
| `description` | string | no | one line in domain language |
| `inputs` | array of io items | yes | `I` |
| `outputs` | array of io items | yes | `O` |
| `preconditions` | array of conditions | yes | `P` |
| `effects` | array of effects | yes | `E` |
| `constraints` | array of conditions | yes | `K_i` over inputs or state |
| `resources` | array of strings | yes | `R_i`, ids declared in the sheet's `resources` |
| `quality` | object | yes | `Q` (section 3.5) |
| `reliability` | number 0..1 | yes | `Rel` |
| `availability` | boolean, 0/1 or window object | yes | `A` or `A(t)` (section 3.6) |
| `mechanism` | object | yes | `M` (section 3.7) |
| `roles` | array of strings | no | roles allowed to execute, for example `patient`, `nurse`, `reviewer` |
| `state_delta_hint` | object | no | informational net delta; the encoder computes the delta from `P` and `E` anyway |

### 3.1 Inputs and outputs

Each entry of `inputs` and `outputs`:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `name` | string | yes | parameter name as the module endpoint spells it |
| `type` | string | yes | value type, the module side names are used (`string`, `boolean`, `integer`, `real`, `enum`, ...) |
| `domain` | string or array | yes | one line description or the list of allowed values |
| `required` | boolean | no, default `true` | a missing required input fails validation; an optional input needs no binding |

The input-output compatibility check binds every required input of the later capability against
the outputs of the earlier one, its effects and the initial state; an unbound required input
makes the pair unknown (see `documents/03_EMBEDDING_DESIGN.md` for the scores and
`documents/04_MAPPING_AND_ADAPTERS.md` for the adapter synthesis that renames fields).

### 3.2 Conditions

A condition is `{"variable": ..., "op": ..., "value": ...}` with operators
`=`, `!=`, `<`, `<=`, `>`, `>=`, `in`.

- `=` and `!=`: equality against a typed literal.
- `<`, `<=`, `>`, `>=`: numeric comparison, no open bounds issue arises because the evaluator
  works over interval domains.
- `in`: membership; the value is an array of literals.

Conditions appear as preconditions, capability constraints and module goal entries.

### 3.3 Effects

An effect is `{"variable": ..., "op": ..., "value": ...}` with operators
`SET`, `INCREMENT`, `DECREMENT`, `DELETE`.

- `SET` assigns a literal.
- `INCREMENT` and `DECREMENT` shift a numeric variable; over an interval domain they shift both
  bounds.
- `DELETE` removes the binding.

Authoring rule: preconditions and effects reference declared state variables only, and effect
values are literal constants. An effect whose value depends on the request (for example a
summary whose text is generated from the document) is described in the capability description
instead of being faked as a literal; the state variable it touches is still declared and named
in the description when the fact is state relevant.

### 3.4 Capability constraints

Same condition form as preconditions. They express parameter level rules (ranges, allowed
memberships) that the module endpoint enforces with a 400 validation error; the compatibility
engine treats a constraint that provably fails as a hard failure of the pair.

### 3.5 Quality attributes

`quality` holds non-negative numbers:

| Attribute | Unit | Meaning |
| --- | --- | --- |
| `time_ms` | milliseconds | expected execution time |
| `money` | abstract money units | expected monetary cost |
| `resource` | 0..1 fraction | normalized resource pressure |
| `risk` | 0..1 | expected risk of the operation |
| `energy` | abstract energy units | expected energy cost |

Extra numeric attributes are allowed and preserved (the parser keeps them in `cost.extra`);
`risk` is validated into `[0, 1]`.

### 3.6 Availability

Three forms:

- `true` / `false`: the capability is always or never available.
- `0` / `1`: numeric form of the same fact.
- `{"always": false, "windows": [{"days": ["mon", "fri"], "from": "08:00", "to": "16:30", "timezone": "local"}]}`:
  time windowed availability `A(t)`. `always` defaults to true; the `windows` list overrides
  it by day and time. `from` and `to` are `HH:MM` in 24 hour form; `days` uses three letter
  names.

The compatibility engine's availability check evaluates a windowed capability at a weekday plus
minute value supplied by the evaluation context; a capability outside its window fails that
check.

### 3.7 Mechanism

`mechanism.kind` names the execution mechanism; the fields used by each kind are:

| Kind | Fields | Meaning |
| --- | --- | --- |
| `API` | `method`, `endpoint` | HTTP call against `module.base_url` |
| `DATABASE` | `operation`, `table` | SQL statement against the module database; canonical operations are `insert`, `update`, `select_one`, with `create`, `set`, `select`, `query`, `read` accepted as aliases |
| `GUI` | `action`, `component`, `page` | form interaction; `action` is `CLICK`, `SUBMIT`, `SELECT` or `NAVIGATE` |
| `EVENT` | `trigger`, `handler` | event delivery |
| `MESSAGE` | `topic`, `queue` | message publication |
| `FUNCTION` | `function`, `module_path` | in-process function call |
| `FILE` | `path`, `format` | file artifact; formats `csv`, `json`, `text`, `binary` |
| `COMPUTATION` | `expression`, `output_artifact` | pure computation, no external effect |
| `SERVICE` | `service`, `base_url` | remote service call |

`notes` is free text on any mechanism. A capability's `type` and its `mechanism.kind` are
normally equal; the resolver's delivery kind tie break compares the kind of a candidate against
the `type` declared by the requirement, which is how `register_pat` (an API call) is separated
from the equally scored `pat_reg_form` (a GUI form) in the alias application.

## 4. Validation

`careweave_cli validate <sheet>...` parses each sheet with schema validation enabled and prints
either one `ok` line with the capability and state variable counts or every issue with its JSON
pointer. The same validation runs in the module build (each module serves its `spec.json` and
its tests validate it), in the corpus test and in the dataset conformance test.

The parser checks, beyond the schema: undeclared state variables in conditions and effects
(strict variable checking), duplicate capability ids, empty names, reference integrity of
capability resource lists against the sheet's `resources`, reliability range and issue
locations for every finding.

## 5. Worked example

The smallest complete sheet in the repository is a requirement sheet:

```yaml
spec_version: "1.0"
module:
  module_id: requirement-register-pat
  version: "1.0"
  domain: hospital
  port: 5201
  base_url: http://127.0.0.1:5201
  health: /health
state_schema:
  - name: Patient.registered
    type: boolean
    domain: [false, true]
    kind: flag
initial_state:
  Patient.registered: false
resources: []
constraints: []
goal:
  - variable: Patient.registered
    op: "="
    value: true
capabilities:
  - id: REQ-RegisterPat
    name: register_pat
    type: API
    inputs:
      - name: name
        type: string
        domain: patient full name
        required: true
    outputs:
      - name: patient_id
        type: string
        domain: new identifier
    preconditions: []
    effects:
      - variable: Patient.registered
        op: SET
        value: true
    constraints: []
    resources: []
    quality: {}
    reliability: 1.0
    availability: true
    mechanism:
      kind: API
      method: POST
      endpoint: /register_pat
```

The full sheets in `specs/app/` follow the same shape with more capabilities; the field
reference above covers every one of them.
