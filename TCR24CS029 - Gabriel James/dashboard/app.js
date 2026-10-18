"use strict";

// The dashboard is one static page; every panel calls the gateway management API and renders
// the JSON it answers. Nothing here reaches beyond the local gateway: all requests use relative
// paths and all styling is local.

const $ = (id) => document.getElementById(id);

let sheets = [];
let registryRows = [];

async function api(path, method = "GET", body = null) {
  const options = { method, headers: {} };
  if (body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = { error: "the gateway answered a body that is not JSON" };
  }
  return { status: response.status, ok: response.ok, json: payload };
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character]));
}

function render(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return esc(JSON.stringify(value));
  return esc(String(value));
}

function fixed(value, digits = 4) {
  if (typeof value !== "number" || !isFinite(value)) return render(value);
  return esc(value.toFixed(digits));
}

function badge(ok, text, warn = false) {
  const kind = ok ? "good" : warn ? "warn" : "bad";
  return '<span class="badge ' + kind + '">' + esc(text) + "</span>";
}

function notice(container, message) {
  container.innerHTML = '<p class="muted">' + esc(message) + "</p>";
}

function table(headers, rows, rowClass) {
  if (!Array.isArray(rows) || !rows.length) return '<p class="muted">no rows</p>';
  let html = "<table><thead><tr>";
  for (const header of headers) html += "<th>" + esc(header.label) + "</th>";
  html += "</tr></thead><tbody>";
  for (const row of rows) {
    const className = rowClass ? rowClass(row) : "";
    html += className ? '<tr class="' + className + '">' : "<tr>";
    for (const header of headers) html += "<td>" + header.cell(row) + "</td>";
    html += "</tr>";
  }
  return html + "</tbody></table>";
}

function objectsTable(rows, order) {
  if (!Array.isArray(rows) || !rows.length) return '<p class="muted">no rows</p>';
  const keys = order && order.length
    ? order.filter((key) => rows.some((row) => key in row))
    : Object.keys(rows[0]);
  return table(keys.map((key) => ({ label: key, cell: (row) => render(row[key]) })), rows);
}

function scalarTable(object) {
  if (!object || typeof object !== "object") return "";
  const rows = Object.keys(object).map((key) => ({ key, value: object[key] }));
  return table(
    [
      { label: "field", cell: (row) => "<code>" + esc(row.key) + "</code>" },
      { label: "value", cell: (row) => render(row.value) },
    ],
    rows
  );
}

function traceList(lines) {
  if (!Array.isArray(lines) || !lines.length) return "";
  return '<ul class="trace">' + lines.map((line) => "<li>" + esc(line) + "</li>").join("") + "</ul>";
}

// ---- sheets and selects ----

async function loadSheets() {
  const response = await api("/api/sheets");
  if (!response.ok || !Array.isArray(response.json)) {
    sheets = [];
    return;
  }
  sheets = response.json;
}

function fillSheetSelect(id, kinds) {
  const select = $(id);
  if (!select) return;
  const rows = sheets.filter((sheet) => !kinds || kinds.includes(sheet.kind));
  select.innerHTML = rows
    .map((sheet) => {
      const suffix = sheet.capability_id
        ? " [" + sheet.capability_id + "]"
        : sheet.steps
          ? " [" + sheet.steps + " steps]"
          : "";
      return '<option value="' + esc(sheet.path) + '">' + esc(sheet.path + suffix) + "</option>";
    })
    .join("");
}

// ---- modules ----

async function loadModules() {
  const response = await api("/api/modules");
  if (!Array.isArray(response.json)) {
    $("status_line").textContent = "the gateway answered " + response.status;
    notice($("modules_result"), response.json && response.json.error ? response.json.error : "modules unavailable");
    return;
  }
  const rows = response.json;
  const healthy = rows.filter((module) => module.healthy).length;
  $("status_line").textContent = healthy + " of " + rows.length + " modules healthy";
  $("modules_result").innerHTML = table(
    [
      { label: "Module", cell: (row) => "<code>" + esc(row.module_id) + "</code>" },
      { label: "Available", cell: (row) => (row.available ? "yes" : "no") },
      {
        label: "Healthy",
        cell: (row) =>
          row.healthy ? badge(true, "yes") : badge(false, "no"),
      },
      { label: "Capabilities", cell: (row) => render(row.capabilities) },
      { label: "Base", cell: (row) => "<code>" + esc(row.base_url) + "</code>" },
      { label: "Spec source", cell: (row) => render(row.spec_source) },
      { label: "Message", cell: (row) => render(row.health_message) },
    ],
    rows
  );
  fillPreferredModules(rows);
  fillBundleModules(rows);
}

function fillPreferredModules(rows) {
  const options = ['<option value="">automatic</option>'];
  for (const row of rows) {
    options.push('<option value="' + esc(row.module_id) + '">' + esc(row.module_id) + "</option>");
  }
  $("builder_preferred").innerHTML = options.join("");
  const selected = $("adapter_module").value;
  $("adapter_module").innerHTML = rows
    .map((row) => '<option value="' + esc(row.module_id) + '">' + esc(row.module_id) + "</option>")
    .join("");
  if (selected) $("adapter_module").value = selected;
  fillAdapterCapabilities();
}

// ---- registry ----

async function loadRegistry() {
  const response = await api("/api/registry");
  registryRows = Array.isArray(response.json) ? response.json : [];
  renderRegistry();
}

function renderRegistry() {
  const filter = $("registry_filter").value.trim().toLowerCase();
  const rows = filter
    ? registryRows.filter((row) =>
        [row.module_id, row.capability_id, row.capability_name, row.capability_type]
          .join(" ")
          .toLowerCase()
          .includes(filter)
      )
    : registryRows;
  $("registry_result").innerHTML =
    '<p class="muted">' + rows.length + " of " + registryRows.length + " capabilities</p>" +
    table(
      [
        { label: "Module", cell: (row) => "<code>" + esc(row.module_id) + "</code>" },
        { label: "Id", cell: (row) => "<code>" + esc(row.capability_id) + "</code>" },
        { label: "Name", cell: (row) => esc(row.capability_name) },
        { label: "Type", cell: (row) => esc(row.capability_type) },
        { label: "Endpoint", cell: (row) => render(row.endpoint) },
      ],
      rows
    );
}

function fillAdapterCapabilities() {
  const moduleId = $("adapter_module").value;
  const rows = registryRows.filter((row) => !moduleId || row.module_id === moduleId);
  $("adapter_capability").innerHTML = rows
    .map(
      (row) =>
        '<option value="' + esc(row.capability_id) + '">' +
        esc(row.capability_id + " (" + row.capability_name + ")") +
        "</option>"
    )
    .join("");
}

// ---- embedding explorer ----

async function encodeSheet() {
  const sheet = $("embed_sheet").value;
  if (!sheet) {
    notice($("embed_result"), "no sheet selected");
    return;
  }
  const response = await api("/api/embed", "POST", { sheet });
  const body = response.json;
  if (!response.ok) {
    notice($("embed_result"), body.error || "embedding failed");
    return;
  }
  const capabilities = body.capabilities || [];
  let html = table(
    [
      { label: "Id", cell: (row) => "<code>" + esc(row.id) + "</code>" },
      { label: "Name", cell: (row) => esc(row.name) },
      { label: "Dimensions", cell: (row) => render(row.dimensions) },
      { label: "Blocks", cell: (row) => render(Object.keys(row.blocks || {}).length) },
    ],
    capabilities
  );
  for (const capability of capabilities) {
    const blocks = Object.keys(capability.blocks || {}).map((name) => ({
      name,
      size: capability.blocks[name].size,
      norm: capability.blocks[name].norm,
    }));
    html +=
      "<h3><code>" + esc(capability.id) + "</code> blocks</h3>" +
      table(
        [
          { label: "Block", cell: (row) => esc(row.name) },
          { label: "Dimensions", cell: (row) => render(row.size) },
          { label: "Norm", cell: (row) => fixed(row.norm) },
        ],
        blocks
      );
  }
  $("embed_result").innerHTML = html;
  const options = capabilities
    .map((capability) => '<option value="' + esc(capability.id) + '">' + esc(capability.id) + "</option>")
    .join("");
  $("compare_left").innerHTML = options;
  $("compare_right").innerHTML = options;
  if (capabilities.length > 1) $("compare_right").selectedIndex = 1;
}

async function compareCapabilities() {
  const sheet = $("embed_sheet").value;
  const left = $("compare_left").value;
  const right = $("compare_right").value;
  if (!sheet || !left || !right) {
    notice($("compare_result"), "pick a sheet and two capabilities");
    return;
  }
  const response = await api("/api/embed/compare", "POST", { sheet, left, right });
  const body = response.json;
  if (!response.ok) {
    notice($("compare_result"), body.error || "comparison failed");
    return;
  }
  const blocks = Object.keys(body.blocks || {}).map((name) => ({ name, value: body.blocks[name] }));
  $("compare_result").innerHTML =
    '<p class="kv">total <code>' + fixed(body.total) + "</code>, functional <code>" +
    fixed(body.functional) + "</code>, implementation <code>" + fixed(body.implementation) +
    "</code></p>" +
    table(
      [
        { label: "Block", cell: (row) => esc(row.name) },
        { label: "Cosine", cell: (row) => fixed(row.value) },
      ],
      blocks
    );
}

// ---- mapping studio ----

async function resolveSheet() {
  const requirement = $("resolve_sheet").value;
  if (!requirement) {
    notice($("resolve_result"), "no requirement selected");
    return;
  }
  const response = await api("/api/resolve", "POST", { requirement });
  if (!response.ok) {
    notice($("resolve_result"), response.json.error || "resolve failed");
    return;
  }
  const rows = response.json;
  const ambiguous = rows.filter((row) => row.ambiguous).length;
  $("resolve_result").innerHTML =
    '<p class="muted">' + rows.length + " candidates, " + ambiguous +
    " inside the ambiguity margin</p>" +
    table(
      [
        { label: "Module", cell: (row) => "<code>" + esc(row.module_id) + "</code>" },
        { label: "Id", cell: (row) => "<code>" + esc(row.capability_id) + "</code>" },
        { label: "Name", cell: (row) => esc(row.capability_name) },
        { label: "Type", cell: (row) => esc(row.capability_type) },
        { label: "Endpoint", cell: (row) => render(row.endpoint) },
        { label: "Total", cell: (row) => fixed(row.total) },
        { label: "Margin", cell: (row) => fixed(row.margin) },
        {
          label: "Ambiguous",
          cell: (row) => (row.ambiguous ? '<span class="badge warn">near tie</span>' : ""),
        },
        {
          label: "Adapter",
          cell: (row) =>
            '<button class="row-action" data-requirement="' + esc(requirement) +
            '" data-module="' + esc(row.module_id) + '" data-capability="' + esc(row.capability_id) +
            '">adapter</button>',
        },
      ],
      rows,
      (row) => (row.ambiguous ? "ambiguous" : "")
    );
}

function adapterFromRow(button) {
  $("adapter_sheet").value = button.dataset.requirement;
  $("adapter_module").value = button.dataset.module;
  fillAdapterCapabilities();
  $("adapter_capability").value = button.dataset.capability;
  activate("adapter");
  synthesizeAdapter();
}

// ---- requirement builder ----

async function builderSheetChanged() {
  const requirement = $("builder_sheet").value;
  if (!requirement) {
    $("builder_inputs").innerHTML = "";
    return;
  }
  const response = await api("/api/sheet?path=" + encodeURIComponent(requirement));
  if (!response.ok) {
    notice($("builder_result"), response.json.error || "sheet unavailable");
    return;
  }
  const model = response.json.model || {};
  const capability = (model.capabilities || [])[0] || {};
  const inputs = capability.inputs || [];
  if (!inputs.length) {
    $("builder_inputs").innerHTML = '<p class="muted">this capability declares no inputs</p>';
    return;
  }
  $("builder_inputs").innerHTML = inputs
    .map((input) => {
      const domain = typeof input.domain === "string"
        ? input.domain
        : input.domain
          ? JSON.stringify(input.domain)
          : "";
      const optional = input.required === false ? " (optional)" : "";
      return (
        "<label>" + esc(input.name + optional) +
        '<input data-input="' + esc(input.name) + '" placeholder="' + esc(domain) + '"></label>'
      );
    })
    .join("");
}

async function runRequirement() {
  const requirement = $("builder_sheet").value;
  if (!requirement) return;
  const inputs = {};
  document.querySelectorAll("#builder_inputs input[data-input]").forEach((input) => {
    if (input.value !== "") inputs[input.dataset.input] = input.value;
  });
  const payload = { requirement, inputs };
  const preferred = $("builder_preferred").value;
  if (preferred) payload.preferred_modules = [preferred];
  const response = await api("/api/call", "POST", payload);
  const body = response.json;
  let html = "<p>" + badge(body.ok === true, body.ok === true ? "ok" : "failed") +
    " http " + esc(response.status) + "</p>";
  html +=
    '<p class="kv">module <code>' + esc(body.module_id || "") + "</code>, capability <code>" +
    esc(body.capability_id || "") + "</code>, adapter <code>" + esc(body.adapter_id || "") +
    "</code>, attempts " + render(body.attempts) + ", fallback " + render(body.fallback_used) +
    ", module called " + render(body.module_called) + "</p>";
  if (body.error) html += "<p>" + esc(body.error) + "</p>";
  if (body.outputs) html += "<h3>Outputs</h3><pre>" + esc(JSON.stringify(body.outputs, null, 2)) + "</pre>";
  if (body.trace && body.trace.length) html += "<h3>Trace</h3>" + traceList(body.trace);
  $("builder_result").innerHTML = html;
}

// ---- adapter studio ----

async function synthesizeAdapter() {
  const requirement = $("adapter_sheet").value;
  const moduleId = $("adapter_module").value;
  const capabilityId = $("adapter_capability").value;
  if (!requirement || !moduleId || !capabilityId) {
    notice($("adapter_result"), "pick a requirement, module and capability");
    return;
  }
  const response = await api("/api/adapter", "POST", {
    requirement,
    module: moduleId,
    capability: capabilityId,
  });
  const body = response.json;
  let html = "<p>" + badge(body.ok === true, body.ok === true ? "synthesized" : "rejected") + "</p>";
  if (!body.ok) {
    html += "<p>" + esc(body.error || body.message || "no adapter") + "</p>";
    $("adapter_result").innerHTML = html;
    return;
  }
  const adapter = body.adapter || {};
  html += scalarTable(body.score_parts);
  html +=
    '<p class="kv">adapter <code>' + esc(adapter.id) + "</code> from <code>" +
    esc(adapter.requirementId) + "</code> to <code>" + esc(adapter.targetCapabilityId) +
    "</code> in module <code>" + esc(adapter.targetModule) + "</code>, transport <code>" +
    esc(adapter.transportKind) + "</code>, confidence <code>" + fixed(adapter.confidence) +
    "</code></p>";
  const inputs = (adapter.inputMap || []).map((mapping) => ({
    from: mapping.from,
    to: mapping.to,
    transform: mapping.transform,
    required: mapping.required === false ? "optional" : "required",
  }));
  const outputs = (adapter.outputMap || []).map((mapping) => ({
    from: mapping.from,
    to: mapping.to,
    transform: mapping.transform,
  }));
  html += "<h3>Input bindings</h3>" + table(
    [
      { label: "Requirement input", cell: (row) => "<code>" + esc(row.from) + "</code>" },
      { label: "Provider input", cell: (row) => "<code>" + esc(row.to) + "</code>" },
      { label: "Transform", cell: (row) => esc(row.transform) },
      { label: "Requirement", cell: (row) => esc(row.required) },
    ],
    inputs
  );
  html += "<h3>Output bindings</h3>" + table(
    [
      { label: "Provider output", cell: (row) => "<code>" + esc(row.from) + "</code>" },
      { label: "Requirement output", cell: (row) => "<code>" + esc(row.to) + "</code>" },
      { label: "Transform", cell: (row) => esc(row.transform) },
    ],
    outputs
  );
  if (adapter.explanation && adapter.explanation.length) {
    html += "<h3>Explanation</h3>" + traceList(adapter.explanation);
  }
  $("adapter_result").innerHTML = html;
}

// ---- plan view ----

async function runPlan() {
  const sheet = $("plan_sheet").value;
  if (!sheet) return;
  const payload = {
    sheet,
    strategy: $("plan_strategy").value,
    max_depth: Number($("plan_depth").value) || 6,
    backward: $("plan_backward").checked,
  };
  const goalsText = $("plan_goals").value.trim();
  if (goalsText) {
    try {
      payload.goals = JSON.parse(goalsText);
    } catch (error) {
      notice($("plan_result"), "the goal override is not valid JSON");
      return;
    }
  }
  const response = await api("/api/plan", "POST", payload);
  const body = response.json;
  let html = "<p>" + badge(body.found === true,
    body.found ? (body.validated ? "plan found and validated" : "plan found, not validated") : "no plan",
    !body.found) + "</p>";
  if (body.reason) html += "<p>" + esc(body.reason) + "</p>";
  html += table(
    [
      { label: "Step", cell: (row) => render(body.steps.indexOf(row) + 1) },
      { label: "Capability", cell: (row) => "<code>" + esc(row.capability_id) + "</code>" },
      { label: "Name", cell: (row) => esc(row.capability_name) },
      { label: "Establishes", cell: (row) => render(row.established) },
      { label: "Consumes", cell: (row) => render(row.consumed_preconditions) },
    ],
    body.steps || []
  );
  html +=
    '<p class="kv">depth ' + render(body.depth) + ", expanded " + render(body.expanded_states) +
    ", explored " + render(body.explored_states) + ", time " + fixed(body.total_time_ms, 1) +
    " ms, money " + fixed(body.total_money, 2) + ", risk " + fixed(body.total_risk) +
    ", reliability " + fixed(body.total_reliability) + "</p>";
  if (body.explanation) html += "<pre>" + esc(body.explanation) + "</pre>";
  if (body.note) html += '<p class="muted">' + esc(body.note) + "</p>";
  $("plan_result").innerHTML = html;
}

// ---- bundle builder ----

function fillBundleModules(rows) {
  const container = $("bundle_modules");
  if (!container) return;
  container.innerHTML =
    rows
      .map(
        (row) =>
          '<label class="check"><input type="checkbox" data-module="' + esc(row.module_id) +
          '" checked> <code>' + esc(row.module_id) + "</code></label>"
      )
      .join("") || '<p class="muted">no modules discovered</p>';
}

function fillBundleWorkflows() {
  const container = $("bundle_workflows");
  if (!container) return;
  const rows = sheets.filter((sheet) => sheet.kind === "workflow");
  container.innerHTML =
    rows
      .map((row) => {
        const name = row.id || row.path.split("/").pop().replace(/\.json$/, "");
        return '<label class="check"><input type="checkbox" data-workflow="' + esc(name) +
          '" checked> <code>' + esc(name) + "</code></label>";
      })
      .join("") || '<p class="muted">no workflow sheets</p>';
}

async function buildBundle() {
  const payload = { out: $("bundle_out").value.trim() || "dist/careweave-mini" };
  if ($("bundle_no_dashboard").checked) payload.no_dashboard = true;
  const moduleBoxes = Array.from(document.querySelectorAll("#bundle_modules input[data-module]"));
  const chosenModules = moduleBoxes.filter((box) => box.checked).map((box) => box.dataset.module);
  if (moduleBoxes.length && !chosenModules.length) {
    notice($("bundle_result"), "pick at least one module for the bundle");
    return;
  }
  if (chosenModules.length && chosenModules.length < moduleBoxes.length) {
    payload.modules = chosenModules;
  }
  const workflowBoxes = Array.from(
    document.querySelectorAll("#bundle_workflows input[data-workflow]")
  );
  const chosenWorkflows = workflowBoxes
    .filter((box) => box.checked)
    .map((box) => box.dataset.workflow);
  if (workflowBoxes.length && !chosenWorkflows.length) {
    payload.no_workflows = true;
  } else if (chosenWorkflows.length && chosenWorkflows.length < workflowBoxes.length) {
    payload.workflows = chosenWorkflows;
  }
  notice($("bundle_result"), "assembling the bundle, this can take a few seconds");
  const response = await api("/api/bundle", "POST", payload);
  const body = response.json;
  let html = "<p>" + badge(response.ok, response.ok ? "bundle assembled" : "bundle failed") + "</p>";
  const closure = (body && body.closure_added) || [];
  if (closure.length) {
    html +=
      '<p class="muted">added by workflow references: ' +
      closure.map((row) => esc(row.module + " (" + row.reason + ")")).join(", ") + "</p>";
  }
  html += "<pre>" + esc(JSON.stringify(body, null, 2)) + "</pre>";
  if (response.ok) {
    html += '<p class="muted">start it with scripts/setup.sh once, then scripts/start.sh inside ' +
      esc(body.out_dir || payload.out) + "</p>";
  }
  $("bundle_result").innerHTML = html;
}

// ---- workflow runner ----

async function runWorkflow() {
  const workflow = $("workflow_select").value;
  if (!workflow) return;
  notice($("workflow_result"), "running the workflow");
  const response = await api("/api/workflow", "POST", { workflow });
  const body = response.json;
  const steps = body.steps || [];
  let html = "<p>" + badge(body.ok === true, body.ok === true ? "workflow ok" : "workflow failed") +
    " http " + esc(response.status) + "</p>";
  if (body.error) html += "<p>" + esc(body.error) + "</p>";
  const verdictCell = (row) => {
    const verdict = String(row.verdict || "");
    if (verdict === "compatible" || verdict === "first step") return badge(true, verdict);
    if (verdict === "uncertain") return badge(false, verdict, true);
    if (verdict === "incompatible") return badge(false, verdict);
    return render(verdict);
  };
  html += table(
    [
      { label: "Step", cell: (row) => esc(row.name) },
      { label: "Module", cell: (row) => "<code>" + esc(row.module_id) + "</code>" },
      { label: "Capability", cell: (row) => "<code>" + esc(row.capability_id) + "</code>" },
      { label: "Verdict", cell: verdictCell },
      {
        label: "Result",
        cell: (row) =>
          row.call && row.call.ok
            ? badge(true, "called")
            : badge(false, (row.call && row.call.error) || "failed"),
      },
      {
        label: "Outputs",
        cell: (row) => render(row.call ? row.call.outputs : ""),
      },
    ],
    steps
  );
  for (const step of steps) {
    const lines = (step.attempts || []).concat(step.call && step.call.trace ? step.call.trace : []);
    if (lines.length) {
      html += "<h3>" + esc(step.name) + " attempts</h3>" + traceList(lines);
    }
  }
  $("workflow_result").innerHTML = html;
}

// ---- experiments ----

async function loadExperiments() {
  notice($("experiments_result"), "loading the frozen results");
  const response = await api("/api/experiments");
  if (!response.ok) {
    notice($("experiments_result"), response.json.error || "no results");
    return;
  }
  const body = response.json;
  let html = "";
  const evaluation = body.evaluation || {};
  if (Array.isArray(evaluation.criteria)) {
    html += "<h3>Evaluation criteria</h3>" + table(
      [
        { label: "#", cell: (row) => render(row.number) },
        { label: "Property", cell: (row) => esc(row.property) },
        { label: "Measurement", cell: (row) => esc(row.measurement) },
        { label: "Value", cell: (row) => esc(row.value) },
        { label: "Conclusion", cell: (row) => esc(row.conclusion) },
      ],
      evaluation.criteria
    );
  }
  if (evaluation.raw) {
    html += "<h3>Evaluation raw metrics</h3>" + scalarTable(evaluation.raw);
  }
  const experiments = body.experiments || {};
  for (const name of Object.keys(experiments)) {
    const document = experiments[name] || {};
    html += "<h3>" + esc(name) + "</h3>";
    html += '<p class="kv">' + esc(document.experiment || "") +
      (document.pattern ? ", pattern " + esc(document.pattern) : "") + "</p>";
    if (document.metrics) html += scalarTable(document.metrics);
    if (document.dataset) {
      const pairs = Array.isArray(document.dataset.pairs) ? document.dataset.pairs.length : null;
      html += '<p class="muted">' + (pairs !== null ? pairs + " dataset pairs" : "dataset present") + "</p>";
    }
  }
  $("experiments_result").innerHTML = html;
}

// ---- audit ----

async function loadAudit() {
  const limit = Number($("audit_limit").value) || 100;
  const response = await api("/api/audit?limit=" + limit);
  const rows = Array.isArray(response.json) ? response.json : [];
  $("audit_result").innerHTML = objectsTable(rows, [
    "kind", "operation", "module", "capability", "ok", "status", "attempts", "fallback",
    "latency_ms", "message",
  ]);
}

// ---- tabs and wiring ----

function activate(name) {
  document.querySelectorAll("#tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.panel === name);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === "panel-" + name);
  });
}

function safe(handler) {
  return async (event) => {
    try {
      await handler(event);
    } catch (error) {
      console.error(error);
    }
  };
}

async function init() {
  await loadSheets();
  fillSheetSelect("embed_sheet", ["application", "requirement"]);
  fillSheetSelect("resolve_sheet", ["requirement"]);
  fillSheetSelect("builder_sheet", ["requirement"]);
  fillSheetSelect("adapter_sheet", ["requirement"]);
  fillSheetSelect("plan_sheet", ["application"]);
  fillSheetSelect("workflow_select", ["workflow"]);
  fillBundleWorkflows();
  await loadModules();
  await loadRegistry();
  await resolveSheet();
  await builderSheetChanged();
}

document.querySelectorAll("#tabs button").forEach((button) => {
  button.addEventListener("click", () => activate(button.dataset.panel));
});

$("discover_button").addEventListener("click", safe(async () => {
  await api("/api/discover", "POST", {});
  await loadModules();
  await loadRegistry();
}));
$("refresh_button").addEventListener("click", safe(async () => {
  await loadSheets();
  await loadModules();
  await loadRegistry();
}));
$("registry_filter").addEventListener("input", renderRegistry);
$("embed_sheet").addEventListener("change", safe(encodeSheet));
$("embed_load").addEventListener("click", safe(encodeSheet));
$("compare_button").addEventListener("click", safe(compareCapabilities));
$("resolve_sheet").addEventListener("change", safe(resolveSheet));
$("resolve_run").addEventListener("click", safe(resolveSheet));
$("resolve_result").addEventListener("click", safe(async (event) => {
  const button = event.target.closest("button[data-module]");
  if (button) adapterFromRow(button);
}));
$("builder_sheet").addEventListener("change", safe(builderSheetChanged));
$("builder_run").addEventListener("click", safe(runRequirement));
$("adapter_module").addEventListener("change", fillAdapterCapabilities);
$("adapter_run").addEventListener("click", safe(synthesizeAdapter));
$("plan_run").addEventListener("click", safe(runPlan));
$("bundle_run").addEventListener("click", safe(buildBundle));
$("workflow_run").addEventListener("click", safe(runWorkflow));
$("experiments_load").addEventListener("click", safe(loadExperiments));
$("audit_load").addEventListener("click", safe(loadAudit));

init().catch((error) => console.error(error));
