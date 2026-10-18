/* Patient registry UI behaviour.
 *
 * Forms marked with data-capability-endpoint submit their fields as one JSON object to that
 * endpoint and render the module response convention into the element named by
 * data-result-target (default result_output). Numbers are sent as numbers so the service layer
 * type checks see the declared integer inputs.
 */

async function submitCapabilityForm(form) {
  const endpoint = form.dataset.capabilityEndpoint;
  const targetId = form.dataset.resultTarget || "result_output";
  const output = document.getElementById(targetId);
  const payload = {};
  for (const element of form.elements) {
    if (!element.name || element.disabled) continue;
    const value = element.value.trim();
    if (value === "" && !element.required) continue;
    payload[element.name] = element.type === "number" ? Number(value) : value;
  }
  output.className = "result";
  output.textContent = "calling " + endpoint + " ...";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    output.textContent = JSON.stringify(body, null, 2);
    output.className = response.ok ? "result ok" : "result error";
    document.dispatchEvent(new CustomEvent("careweave:result", { detail: { ok: response.ok, body } }));
    return response.ok;
  } catch (error) {
    output.textContent = "request failed: " + error;
    output.className = "result error";
    return false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  for (const form of document.querySelectorAll("form[data-capability-endpoint]")) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitCapabilityForm(form);
    });
  }
  document.addEventListener("careweave:result", (event) => {
    const form = document.querySelector("form[data-capability-reload='true']");
    if (form && event.detail.ok) {
      window.location.reload();
    }
  });
});
