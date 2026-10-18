# Bundling guide

A bundle is a self contained copy of CareWeave Mini: the modules of the checkout (all seven by
default), the specification sheets, the gateway binary, the dashboard and three scripts. It runs
on the same ports as the development tree and needs nothing from the repository it was built
from.

## 1. Build a bundle

From the repository root:

```
sh scripts/build.sh
./core/build/careweave_cli bundle --root . --out dist/careweave-mini --json
```

The command prints the manifest it wrote:

```
{
  "closure_added": [],
  "dashboard": true,
  "files": 192,
  "gateway_binary": true,
  "modules": 7,
  "ok": true,
  "out_dir": "dist/careweave-mini",
  "requested_modules": [],
  "warnings": [],
  "workflows": [
    "visit.json",
    "visit_legacy.json"
  ]
}
```

`--no-dashboard` leaves the dashboard out (the gateway then serves the management API only).
The dashboard's bundle panel calls the same function through `POST /api/bundle`; it accepts an
`out` destination, the `no_dashboard` switch, module and workflow checkboxes for a trimmed
bundle, and the `no_workflows` switch.

### 1.1 A selected bundle and the workflow closure

`--modules <id,...>` bundles exactly the named modules plus the closure: any module a shipped
workflow binds is added back, because a bundle must stay runnable exactly as shipped. The
bundler reports every addition with its reason. `--workflows <name,...>` ships only the named
sheets (matched by file name stem or `workflow_id`), so the closure follows only those, and
`--no-workflows` ships no workflow sheets at all. `POST /api/bundle` takes the same selection
as `modules`, `workflows` and `no_workflows`.

Observed on the development tree, selecting the two modules of a small clinic:

```
$ ./core/build/careweave_cli bundle --root . --out dist/clinic --modules patient-registry-alt,pos-billing --json
{
  "closure_added": [
    {
      "module": "appointment-queue",
      "reason": "referenced by workflow clinic-visit-legacy"
    },
    {
      "module": "opd-ehr",
      "reason": "referenced by workflow clinic-visit"
    },
    {
      "module": "patient-registry",
      "reason": "referenced by workflow clinic-visit"
    }
  ],
  "dashboard": true,
  "files": 145,
  "gateway_binary": true,
  "modules": 5,
  "ok": true,
  "out_dir": "dist/clinic",
  "requested_modules": [
    "patient-registry-alt",
    "pos-billing"
  ],
  "warnings": [],
  "workflows": [
    "visit.json",
    "visit_legacy.json"
  ]
}
```

Two modules were requested and five were bundled: `appointment-queue` is bound by
`visit_legacy.json`, and `opd-ehr` plus `patient-registry` by `visit.json`. The generated
`scripts/start.sh` starts exactly those five:

```
$ grep start_module dist/clinic/scripts/start.sh
start_module appointment-queue 5002
start_module opd-ehr 5003
start_module patient-registry 5001
start_module patient-registry-alt 5007
start_module pos-billing 5005
```

Unknown module ids, unknown workflow names, a workflow that binds a module the checkout does
not have, and a workflow sheet that is not valid JSON are all refusals that name the problem,
and a refusal writes nothing:

```
$ ./core/build/careweave_cli bundle --root . --out dist/clinic --modules ghost
fail: no module with id ghost is in this checkout (known ids: appointment-queue, legacy-lab-service, opd-ehr, patient-registry, patient-registry-alt, pharmacy-inventory, pos-billing)
$ ./core/build/careweave_cli bundle --root . --out dist/clinic --workflows ghost
fail: no workflow sheet matches ghost (available: visit (clinic-visit), visit_legacy (clinic-visit-legacy))
```

What a complete bundle contains:

```
modules/       the seven module servers, each with its specification and requirements
specs/         specification sheets: applications, requirements, workflows
dashboard/     the static dashboard
bin/           careweave_gateway
scripts/       setup.sh, start.sh, stop.sh
MANIFEST.json  the manifest of everything written
README.txt     the short start guide
```

Excluded on purpose: the virtual environment, runtime databases under `modules/*/data/`, logs,
build directories and any `dist/` directory. A bundle is born clean and seeds itself.

## 2. Run a bundle from a clean shell

The complete sequence, as verified on a fresh copy (output pasted from the run):

```
$ sh scripts/setup.sh
environment ready: .venv
$ sh scripts/start.sh
gateway ready: http://127.0.0.1:5100
modules healthy: 7 of 7
$ curl -sS http://127.0.0.1:5100/health
{"status": "ok", ..., "modules_healthy": 7, "modules_total": 7}
$ curl -sS http://127.0.0.1:5100/ | grep -o "<title>[^<]*</title>"
<title>CareWeave Mini dashboard</title>
$ curl -sS http://127.0.0.1:5001/spec | head -c 80
{"capabilities":[{"availability":{"always":true},"constraints":[],"description":"Register a new
$ sh scripts/stop.sh
stopped pos-billing (pid ...)
```

Steps in detail:

1. `scripts/setup.sh` creates `.venv` next to the bundle root and installs the union of the
   module requirements. It needs network access once; afterwards the bundle runs offline.
2. `scripts/start.sh` starts the seven module servers (each with its own log and pid file under
   `.run/`), starts the gateway with the bundle root, and polls `/health` until all seven
   modules are healthy. Each module seeds its demonstration data at startup, so the pages and
   the APIs answer with real rows immediately.
3. The gateway mounts the bundle's `dashboard/` directory automatically, so
   `http://127.0.0.1:5100/` serves the dashboard and `http://127.0.0.1:5100/health` reports the
   discovery state. `POST /api/discover` refreshes the module discovery at any time.
4. `scripts/stop.sh` stops exactly the processes the bundle started (by the pids it recorded in
   `.run/`) and removes the pid files. Running it twice is safe: the second run says
   "nothing to stop".

The default ports are the development ports: modules 5001 to 5007 and the gateway on 5100. Set
`CAREWEAVE_GATEWAY_PORT` before `scripts/start.sh` to move the gateway. `CAREWEAVE_PYTHON`
overrides the interpreter used by `setup.sh` and `start.sh`.

## 3. Verify a bundle

```
curl -sS http://127.0.0.1:5100/health                      # status ok, 7 of 7
curl -sS http://127.0.0.1:5100/api/modules                 # every module with health
curl -sS -X POST http://127.0.0.1:5100/api/discover        # re-discovery
curl -sS -X POST -H 'Content-Type: application/json' \
     --data '{"mrn": "BND-0001", "full_name": "Bundle Check"}' \
     http://127.0.0.1:5100/api/hospital/register_patient
curl -sS -X POST -H 'Content-Type: application/json' \
     --data '{"workflow": "specs/workflows/visit.json"}' \
     http://127.0.0.1:5100/api/workflow
```

The third command answers with the patient id and the adapter used, the fourth runs the full
seven step clinic visit against the bundle's own modules. Both were exercised on the copy in
section 2, together with the canonical workflows and the dashboard page. A selected bundle
follows the same steps: the gateway probes the seven ports and reports the modules that are not
shipped as unavailable, exactly like the closed client pool in the mapping guide.

## 4. Notes

- A bundle is generated output. The build tree keeps `dist/` out of version control; rebuild
  instead of editing a bundle.
- The manifest records module ids, file count, the requested selection, every closure addition
  with its reason, the shipped workflow sheets, and whether the dashboard and gateway binary
  were written; `test_bundle.cpp` asserts on all of it.
- The bundle's README.txt is the short form of this guide and is what a recipient should read
  first. A selected bundle lists its selection and closure in the README too.
