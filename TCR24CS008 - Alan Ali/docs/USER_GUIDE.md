# Website User Guide

## Quick start: see a result in under two minutes

**Fastest path:** open the live app at https://capability-composition-ml-1.onrender.com and continue with the first step below.

**Running it locally instead?** Start the backend and frontend first (see [Setup and detailed user manual](USER_MANUAL.md)), then open `http://127.0.0.1:5173/` and follow the steps below.

1. Select **Scenario editor** in the sidebar, then keep **Example Scenarios** selected.
2. On **Level 2 · Compatible pair**, click **Load & Run**.
3. The app loads that example into the active backend scenario, opens **Experiments**, and runs the groups automatically. Look for `create-order → make-payment` as a compatible pair. The three-capability, alternative, and operational groups show skip reasons because this example has two capabilities and no alternative group.

The experiment report is calculated by the backend from the loaded scenario; it is not a canned screen.

## Pages in sidebar order

### Overview

**What it shows:** counts for states, goals, capabilities, the initial state's values, goal predicates, and a short capability list with effects, reliability, and availability.

**What you can do:** use **Inspect**, **Analyze**, or **Open explorer** to jump into Capabilities or Relationships.

**Example:** Load **Level 2 · Compatible pair** from Scenario editor, return to Overview, and inspect the `cart-ready` state, `payment-success` goal, and the two available operations.

### Scenario editor

This page has **Example Scenarios** and **Custom Scenario** tabs. Example cards are Level 1 single capability, Level 2 compatible pair, Level 3 full chain, Level 4 branching, and Level 5 everything. **Load & Run** posts the selected bundled example to the backend as the active scenario, then navigates to Experiments and triggers a run. The source JSON file remains unchanged; the active server scenario is the working copy.

In Custom Scenario, edit scenario details, states, goals, and capabilities using structured controls. **Add state**, **Add goal**, **Add capability**, **Add condition**, **Add field**, and **Add item** create entries; remove buttons delete rows. **Validate & save scenario** sends the whole draft to the backend, which validates it and replaces the active in-memory scenario. **Reload backend** discards unsaved draft edits and reloads what is currently active. **Import JSON** loads a file into the form; it does not save until you choose Validate & save. **Download** exports the current draft. An advanced JSON editor is also available.

Variable and value combobox suggestions are drawn from values already present in this scenario's states, goals, preconditions, effects, and constraints. Resource and mechanism-key suggestions are drawn from other current capabilities. Suggestions use browser datalists: you can select a suggestion or type a new value. Smart values parse `true`, `false`, `null`, numbers, and valid JSON-looking values into their formal types.

**Example:** Load **Level 1 · Single capability, single state**, then select **Custom Scenario**. Inspect its `Cart.exists` state value and `Order.exists=true` goal. You can change the state or capability and save the changed active copy; the bundled Level 1 file itself is not edited.

### Capabilities

**What it shows:** a selected capability's formal details, including its type, mechanism, inputs/outputs, preconditions, effects, constraints, resources, costs, reliability, and availability.

**What you can do:** choose a capability, click **Generate vector** to request the backend's named feature dimensions, and choose a state then click **Check applicability** to see whether the capability's preconditions and constraints hold.

**Example:** Load **Level 1 · Single capability, single state**; choose `CreateOrder`, generate its vector, and check applicability against `cart-ready`. Its `Cart.exists=true` and `Cart.item_count>0` preconditions hold in that state.

### Relationships

**What it shows:** separate analyses for capability-pair resemblance and directional compatibility, plus goal relevance and state/goal satisfaction.

**What you can do:** choose a producer and consumer and click **Analyze pair**; inspect the similarity score, section scores, compatibility evidence, and reasons. In the lower panels choose a capability and goal for **Analyze effect relevance**, or a state and goal for **Evaluate state against goal**.

**Example:** Load **Level 2 · Compatible pair**, choose `CreateOrder` as producer and `MakePayment` as consumer, and click **Analyze pair**. The order-created effect supplies the consumer's `Order.exists=true` precondition. Similarity remains a separate number and does not decide compatibility.

### Composition

**What it shows:** an ordered chain builder and, after a successful request, the composite capability, validated handoffs, aggregate metrics, formal details, and encoded vector.

**What you can do:** click capability cards to add or remove them from the chain; selected items are numbered in order. Select at least two, then click **Compose chain**. Rejected links return backend diagnostics. On success, expand or collapse the composite vector.

**Example:** Load **Level 2 · Compatible pair**, open Composition, select only `CreateOrder` followed by `MakePayment` (remove any other selected cards), and click **Compose chain**. The pair has the declared `Order.exists=true` handoff and composes. The default three-item chain can include unrelated items, so check the selected order before composing.

### Experiments

**What it shows:** metrics and seven report groups for compatibility, alternative implementations, goal relevance, operational properties, three-capability composition, formal encoding, and state awareness. Skipped experiments include their reason.

**What you can do:** click **Run all experiments** to calculate a fresh report for the active scenario. Loading an example from Scenario editor runs automatically.

**Example:** Load **Level 5 · Everything** and inspect alternative implementation scores and the irrelevant `GetWeather` operation. A three-capability composition skip is expected with the currently declared handoff predicates; the runner reports what the formal data establishes.

## Custom Scenario editor: the main concepts

States are named snapshots of variables and values, while goals are lists of predicates the application would like to satisfy. Capabilities describe operations through interfaces, preconditions, effects, constraints, resources, costs, reliability, and availability. Combobox suggestions offer existing names and values from the scenario, but you can type new text and do not have to select a suggestion.

Loading an example sends a copy of its bundled JSON to the backend as the active working scenario and runs its experiments. Editing custom fields changes a draft; **Validate & save scenario** submits that draft as the new active backend scenario. Neither action writes changes into the bundled example file. Use **Reload backend** to discard unsaved custom edits.

All active scenario changes reside in backend memory and reset when that process restarts. Use **Download** if you want to save a JSON file of your current draft.

## Glossary

- **State:** a snapshot of named variables and their current values.
- **Goal:** a set of conditions the application wants to become true.
- **Capability:** one operation, service, or composite operation with a declared interface and behavior.
- **Precondition:** a fact that must be true before a capability can be used.
- **Effect:** a fact a capability says it will make true or otherwise establish.
- **Similarity:** a number describing how much two formal feature vectors resemble one another.
- **Compatibility:** a directional check that one capability supplies the next capability's declared handoff requirements.
- **Composition:** an ordered group of compatible capabilities represented as one composite capability.
