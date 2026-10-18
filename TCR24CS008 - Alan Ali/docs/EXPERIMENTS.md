# Experiments

## Method and source

The FastAPI `GET /api/experiments` route calls `run_all_experiments()` on the active scenario. The default comes from `data/scenarios/commerce.json`; the five Level examples are under `data/scenarios/examples/`. The runner discovers candidate pairs and chains from declared formal preconditions, effects, required inputs, and capability types. It does not depend on fixed commerce capability IDs. It returns seven groups: the five required assignment experiments plus state/goal encoding and state awareness.

The captured results below were returned by a running local API at `http://127.0.0.1:8012`. For each dataset, I loaded its JSON using `POST /api/scenario` and then captured `GET /api/experiments`; the API was reset to commerce after the checks. Values below are copied from those responses. Floating-point display is the API's actual output.

## Required experiments and measures

1. **Capability compatibility:** find one compatible and one incompatible ordered pair; report requirement evidence and failure reasons. A pair is directional.
2. **Capability composition:** locate a compatible ordered chain of at least three capabilities, return the composite capability/vector, and measure aggregate cost, reliability, and availability.
3. **Alternative implementations:** identify capabilities with matching precondition/effect signatures but different declared types and compare section-weighted capability cosine.
4. **Goal relevance:** report exact goal-effect overlap, fraction of goal conditions covered, and effect-space cosine for each capability.
5. **Operational attributes:** report declared time, reliability, availability, and, when a chain qualifies, its aggregate cost and products.

The supplementary groups encode the first state and goal and evaluate the first state against the first capability's preconditions and constraints.

## Commerce: captured output excerpt

```json
{
  "scenario_id": "commerce-checkout",
  "experiments": [
    {
      "id": "compatibility",
      "results": {
        "compatible_pair": {
          "compatible": true,
          "producer_id": "create-order-api",
          "consumer_id": "make-payment",
          "evidence": [
            {"requirement": "precondition", "name": "Order.exists", "satisfied": true},
            {"requirement": "input", "name": "order_id", "expected_type": "UUID", "provided_type": "UUID", "satisfied": true}
          ],
          "reasons": []
        },
        "incompatible_pair": {
          "compatible": false,
          "producer_id": "create-order-api",
          "consumer_id": "send-receipt",
          "evidence": [
            {"requirement": "precondition", "name": "Payment.status", "provided": null, "satisfied": false},
            {"requirement": "input", "name": "payment_id", "expected_type": "UUID", "provided_type": null, "satisfied": false}
          ],
          "reasons": [
            "Precondition 'Payment.status' has no matching producer effect",
            "Required input 'payment_id' of type UUID is not provided with a matching type"
          ]
        }
      }
    },
    {
      "id": "three_capability_composition",
      "results": {
        "component_ids": ["create-order-api", "make-payment", "send-receipt"],
        "composite": {
          "reliability": 0.9554985,
          "availability": 0.9398592,
          "cost": {"time_ms": 960.0}
        }
      }
    },
    {
      "id": "alternative_implementations",
      "results": {
        "functional_similarity": {
          "api_database": {"similarity": 0.62915791},
          "api_gui": {"similarity": 0.60934613}
        }
      }
    },
    {
      "id": "goal_relevance",
      "results": {
        "relevant": ["create-order-api", "make-payment", "send-receipt", "create-order-db", "create-order-gui"],
        "irrelevant": ["cancel-cart", "refresh-catalog"]
      }
    }
  ],
  "metrics": {
    "capability_count": 7,
    "state_count": 2,
    "goal_count": 1,
    "embedding_dimensions_observed": 60
  }
}
```

The compatible pair's response had two satisfied checks: consumer precondition `Order.exists=true` was supplied by the producer effect, and required `order_id: UUID` by the producer output. The incompatible pair lacked `Payment.status=SUCCESS` and a `payment_id: UUID` output. The API also returned non-alias pair data: `create-order-db__create-order-gui` similarity was `0.73736739`.

## Level 2 compatible pair: captured output excerpt

```json
{
  "scenario_id": "level-2-compatible-pair",
  "experiments": [
    {
      "id": "compatibility",
      "results": {
        "compatible_pair": {
          "compatible": true,
          "producer_id": "create-order",
          "consumer_id": "make-payment",
          "evidence": [
            {"requirement": "precondition", "name": "Order.exists", "satisfied": true}
          ],
          "reasons": []
        }
      }
    },
    {"id": "three_capability_composition", "skipped": "needs a compatible chain of at least 3 capabilities"},
    {"id": "alternative_implementations", "skipped": "no matching precondition/effect group with differing types"},
    {"id": "operational_properties", "skipped": "needs alternative implementations or a three-capability chain"}
  ],
  "metrics": {
    "capability_count": 2,
    "state_count": 2,
    "goal_count": 1,
    "embedding_dimensions_observed": 22
  }
}
```

With two capabilities, the example can demonstrate compatibility, but groups requiring a longer chain or alternatives have no qualifying input. A skip records why an experiment does not apply; it is not a failed experiment or runtime error.

## Level 3 full-chain example: captured output excerpt

```json
{
  "scenario_id": "level-3-full-chain",
  "experiments": [
    {"id": "three_capability_composition", "skipped": "needs a compatible chain of at least 3 capabilities"},
    {"id": "alternative_implementations", "skipped": "no matching precondition/effect group with differing types"},
    {"id": "operational_properties", "skipped": "needs alternative implementations or a three-capability chain"},
    {"id": "state_awareness", "results": {"applicable": true}}
  ],
  "metrics": {
    "capability_count": 3,
    "state_count": 4,
    "goal_count": 1,
    "embedding_dimensions_observed": 31
  }
}
```

Although its name describes a chain, the runner's formal checks do not find a valid three-link chain in this file. For example, a later stage requiring `Payment.status=NOT_STARTED` needs a matching earlier equality effect; the current prior stage does not declare that effect. The runner bases its result on formal handoff data rather than the example name.

## Level 5 everything example: captured output excerpt

```json
{
  "scenario_id": "level-5-everything",
  "experiments": [
    {"id": "three_capability_composition", "skipped": "needs a compatible chain of at least 3 capabilities"},
    {
      "id": "alternative_implementations",
      "results": {
        "functional_similarity": {
          "api_database": {"similarity": 0.76934296},
          "api_gui": {"similarity": 0.74050302},
          "create-order-database__create-order-gui": {"similarity": 0.67087813}
        }
      }
    },
    {"id": "goal_relevance", "results": {"irrelevant": ["get-weather"]}}
  ],
  "metrics": {
    "capability_count": 6,
    "state_count": 4,
    "goal_count": 1,
    "embedding_dimensions_observed": 45
  }
}
```

Level 5 supplies alternatives and an irrelevant capability, but its declared intermediate preconditions still do not yield a compatible three-stage chain under the current checks.

## Explicit composite dataset

`data/scenarios/composition-example.json` contains two atomic capabilities and a declared `COMPOSITE` with ordered component IDs. I submitted the two atomic entries to `POST /api/compose`; the captured response was `compose:prepare-order->confirm-order`, with one compatible link, reliability `0.9702`, availability `0.9506`, and time `40.0 ms`. The dataset itself was also accepted by `POST /api/experiments/run` as scenario `composition-example` with three capabilities.

## Interpretation and limits

Similarity is representation resemblance, not a compatibility probability. Exact feature-name overlap and the declared category weights shape scores. The goal relevance coverage is a direct matching-effect ratio. The reported scenarios are demonstrations, not statistical validation or a performance benchmark. Costs are declarations from the scenario. Chain reliability and availability multiply as if component outcomes are independent. Results depend on scenario formality: missing effects or typed outputs can make an intended real-world handoff fail the symbolic check.
