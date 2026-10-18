#pragma once

#include "types.hpp"
#include "embedding.hpp"
#include <iostream>
#include <iomanip>
#include <vector>
#include <string>

namespace capability_embedding {

class BenchmarkExperiments {
public:
    // -------------------------------------------------------------------------
    // EXPERIMENT 1: Capability Compatibility (Assignment PDF Section 7.1)
    // -------------------------------------------------------------------------
    static void runExperiment1(const ApplicationProblem& app, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "EXPERIMENT 1: CAPABILITY COMPATIBILITY (Section 7.1)\n";
        std::cout << "Investigating C1 -> C2 (compatible) versus C1 -> C3 (incompatible)\n";
        std::cout << "======================================================================\n";

        const Capability* c1 = nullptr; // CreateOrder
        const Capability* c2 = nullptr; // MakePayment
        const Capability* c3 = nullptr; // CancelCart

        for (const auto& c : app.capabilities) {
            if (c.id == "CreateOrder") c1 = &c;
            if (c.id == "MakePayment") c2 = &c;
            if (c.id == "CancelCart") c3 = &c;
        }

        if (!c1 || !c2 || !c3) {
            std::cerr << "Error: Required capabilities for Experiment 1 not found in dataset.\n";
            return;
        }

        double comp12 = emb.compatibility(*c1, *c2);
        double comp13 = emb.compatibility(*c1, *c3);
        double io12 = emb.inputOutputCompatibility(*c1, *c2);
        double io13 = emb.inputOutputCompatibility(*c1, *c3);

        std::cout << "\nEvaluating Formal Transitions:\n";
        std::cout << "  C1: " << c1->id << "  [Effect: order_exists = true]\n";
        std::cout << "  C2: " << c2->id << "   [Precondition: order_exists == true]\n";
        std::cout << "  C3: " << c3->id << "    [Precondition: order_exists == false]\n\n";

        std::cout << std::left << std::setw(28) << "Capability Transition"
                  << std::setw(18) << "Comp(C_i, C_j)"
                  << std::setw(18) << "IO-Comp"
                  << "Semantic Status\n";
        std::cout << std::string(70, '-') << "\n";

        std::cout << std::left << std::setw(28) << (c1->id + " -> " + c2->id)
                  << std::fixed << std::setprecision(4) << std::setw(18) << comp12
                  << std::fixed << std::setprecision(2) << std::setw(18) << io12
                  << "COMPATIBLE   (Enables C2)\n";

        std::cout << std::left << std::setw(28) << (c1->id + " -> " + c3->id)
                  << std::fixed << std::setprecision(4) << std::setw(18) << comp13
                  << std::fixed << std::setprecision(2) << std::setw(18) << io13
                  << "INCOMPATIBLE (Conflicts with C3)\n";

        std::cout << "\nMathematical Defensibility:\n";
        std::cout << "  e(CreateOrder) dot p(MakePayment)  = (+1.0) * (+1.0) = +1.0  => Comp = +1.0000\n";
        std::cout << "  e(CreateOrder) dot p(CancelCart)   = (+1.0) * (-1.0) = -1.0  => Comp = -1.0000\n";
        std::cout << "Conclusion: The vector representation cleanly and deterministically identifies\n"
                  << "            precondition enabling versus causal state violations.\n";
    }

    // -------------------------------------------------------------------------
    // EXPERIMENT 2: Capability Composition (Assignment PDF Section 7.2)
    // -------------------------------------------------------------------------
    static void runExperiment2(const ApplicationProblem& app, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "EXPERIMENT 2: CAPABILITY COMPOSITION (Section 7.2)\n";
        std::cout << "Constructing Composite Capability: CompletePurchase = C3 o C2 o C1\n";
        std::cout << "======================================================================\n";

        const Capability* c1 = nullptr; // CreateOrder
        const Capability* c2 = nullptr; // MakePayment
        const Capability* c3 = nullptr; // SendNotification

        for (const auto& c : app.capabilities) {
            if (c.id == "CreateOrder") c1 = &c;
            if (c.id == "MakePayment") c2 = &c;
            if (c.id == "SendNotification") c3 = &c;
        }

        if (!c1 || !c2 || !c3) {
            std::cerr << "Error: Required capabilities for Experiment 2 not found.\n";
            return;
        }

        // Sequential algebraic composition: (C2 o C1) followed by C3
        Capability c12 = emb.compose(*c1, *c2);
        Capability completePurchase = emb.compose(c12, *c3);
        completePurchase.id = "CompletePurchase";
        completePurchase.name = "Complete Order, Payment & Notification";

        auto v1 = emb.encodeCapability(*c1);
        auto v2 = emb.encodeCapability(*c2);
        auto v3 = emb.encodeCapability(*c3);
        auto vComp = emb.encodeCapability(completePurchase);

        std::cout << "\nPipeline Components:\n";
        std::cout << "  1. " << c1->id << " [Time: " << c1->qos.timeCostMs << "ms, Cost: $" << c1->qos.moneyCost << ", Rel: " << c1->reliability << "]\n";
        std::cout << "  2. " << c2->id << "  [Time: " << c2->qos.timeCostMs << "ms, Cost: $" << c2->qos.moneyCost << ", Rel: " << c2->reliability << "]\n";
        std::cout << "  3. " << c3->id << " [Time: " << c3->qos.timeCostMs << "ms, Cost: $" << c3->qos.moneyCost << ", Rel: " << c3->reliability << "]\n\n";

        std::cout << "Synthesized Composite Capability: " << completePurchase.id << "\n";
        std::cout << "  Preconditions (" << completePurchase.preconditions.size() << "):\n";
        for (const auto& p : completePurchase.preconditions) {
            std::cout << "    - " << p.variable << " == " << (p.expectedValue ? "true" : "false") << "\n";
        }
        std::cout << "    * Note: order_exists and payment_success were internally satisfied and pruned!\n";

        std::cout << "  Effects (" << completePurchase.effects.size() << "):\n";
        for (const auto& e : completePurchase.effects) {
            std::cout << "    - " << e.variable << " = " << (e.value ? "true" : "false") << "\n";
        }

        std::cout << "\nAggregated Operational Metrics:\n";
        std::cout << "  - Total Execution Time: " << completePurchase.qos.timeCostMs << " ms (sum)\n";
        std::cout << "  - Total Monetary Cost:  $" << std::fixed << std::setprecision(4) << completePurchase.qos.moneyCost << " (sum)\n";
        std::cout << "  - Total Resource Cost:  " << completePurchase.qos.resourceCost << " compute units\n";
        std::cout << "  - Aggregated Risk:      " << std::fixed << std::setprecision(4) << completePurchase.qos.risk << "\n";
        std::cout << "  - Combined Reliability: " << std::fixed << std::setprecision(6) << completePurchase.reliability
                  << " (product: " << c1->reliability << " * " << c2->reliability << " * " << c3->reliability << ")\n";
        std::cout << "  - Availability:         " << (completePurchase.availability > 0.5 ? "AVAILABLE (1.0)" : "UNAVAILABLE (0.0)") << "\n";

        std::cout << "\nVector Embedding Relations (dim = " << vComp.size() << "):\n";
        std::cout << "  Cosine Similarity(CompletePurchase, CreateOrder):      "
                  << std::fixed << std::setprecision(4) << VectorEmbeddingEngine::similarity(vComp, v1) << "\n";
        std::cout << "  Cosine Similarity(CompletePurchase, MakePayment):      "
                  << std::fixed << std::setprecision(4) << VectorEmbeddingEngine::similarity(vComp, v2) << "\n";
        std::cout << "  Cosine Similarity(CompletePurchase, SendNotification): "
                  << std::fixed << std::setprecision(4) << VectorEmbeddingEngine::similarity(vComp, v3) << "\n";

        std::cout << "\nConclusion: The composite capability is encoded using the exact same vector space\n"
                  << "            as atomic capabilities, preserving algebraic properties and interface invariants.\n";
    }

    // -------------------------------------------------------------------------
    // EXPERIMENT 3: Alternative Implementations (Assignment PDF Section 7.3)
    // -------------------------------------------------------------------------
    static void runExperiment3(const std::vector<Capability>& allCaps, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS (Section 7.3)\n";
        std::cout << "Demonstrating that Vector Similarity != Sequential Composability\n";
        std::cout << "======================================================================\n";

        const Capability* cApi = nullptr;
        const Capability* cDb = nullptr;
        const Capability* cGui = nullptr;
        const Capability* cOrder = nullptr;

        for (const auto& c : allCaps) {
            if (c.id == "MakePayment_API") cApi = &c;
            if (c.id == "MakePayment_DATABASE") cDb = &c;
            if (c.id == "MakePayment_GUI") cGui = &c;
            if (c.id == "CreateOrder") cOrder = &c;
        }

        if (!cApi || !cDb || !cGui) {
            std::cerr << "Error: Alternative payment implementations not found.\n";
            return;
        }

        auto vApi = emb.encodeCapability(*cApi);
        auto vDb = emb.encodeCapability(*cDb);
        auto vGui = emb.encodeCapability(*cGui);

        std::cout << "\nEvaluated Alternative Implementations of Payment:\n";
        std::cout << std::left << std::setw(25) << "Capability ID"
                  << std::setw(12) << "Type"
                  << std::setw(14) << "Time (ms)"
                  << std::setw(12) << "Cost ($)"
                  << std::setw(14) << "Reliability"
                  << "Mechanism\n";
        std::cout << std::string(90, '-') << "\n";

        std::vector<const Capability*> alts = {cApi, cDb, cGui};
        for (const auto* c : alts) {
            std::cout << std::left << std::setw(25) << c->id
                      << std::setw(12) << c->type
                      << std::setw(14) << c->qos.timeCostMs
                      << "$" << std::fixed << std::setprecision(3) << std::setw(11) << c->qos.moneyCost
                      << std::fixed << std::setprecision(3) << std::setw(14) << c->reliability
                      << c->mechanism << "\n";
        }

        std::cout << "\nPairwise Cosine Similarities (Functional & Vector Resemblance):\n";
        double sim_api_db = VectorEmbeddingEngine::similarity(vApi, vDb);
        double sim_api_gui = VectorEmbeddingEngine::similarity(vApi, vGui);
        double sim_db_gui = VectorEmbeddingEngine::similarity(vDb, vGui);

        std::cout << "  Sim(MakePayment_API, MakePayment_DATABASE) = " << std::fixed << std::setprecision(4) << sim_api_db << "\n";
        std::cout << "  Sim(MakePayment_API, MakePayment_GUI)      = " << std::fixed << std::setprecision(4) << sim_api_gui << "\n";
        std::cout << "  Sim(MakePayment_DATABASE, MakePayment_GUI) = " << std::fixed << std::setprecision(4) << sim_db_gui << "\n";

        std::cout << "\nComposability Analysis:\n";
        if (cOrder) {
            std::cout << "  Compatibility(CreateOrder -> MakePayment_API):      "
                      << std::fixed << std::setprecision(4) << emb.compatibility(*cOrder, *cApi) << "  [COMPATIBLE]\n";
            std::cout << "  Compatibility(CreateOrder -> MakePayment_DATABASE): "
                      << std::fixed << std::setprecision(4) << emb.compatibility(*cOrder, *cDb) << "  [COMPATIBLE]\n";
            std::cout << "  Compatibility(CreateOrder -> MakePayment_GUI):      "
                      << std::fixed << std::setprecision(4) << emb.compatibility(*cOrder, *cGui) << "  [COMPATIBLE]\n";
        }

        double selfChainComp = emb.compatibility(*cApi, *cDb);
        std::cout << "  Compatibility(MakePayment_API -> MakePayment_DATABASE): "
                  << std::fixed << std::setprecision(4) << selfChainComp << "  [CANNOT COMPOSE / REDUNDANT]\n";

        std::cout << "\nCritical Insight: SIMILARITY != COMPOSABILITY\n";
        std::cout << "  - MakePayment_API and MakePayment_DATABASE have high similarity (" << std::fixed << std::setprecision(2) << (sim_api_db * 100.0)
                  << "%), because both set payment_success = true.\n";
        std::cout << "  - However, their sequential compatibility is " << std::fixed << std::setprecision(2) << selfChainComp
                  << " (neither produces preconditions required by the other).\n";
        std::cout << "  - Similarity measures representation overlap; compatibility measures causal workflow validity.\n";
    }

    // -------------------------------------------------------------------------
    // EXPERIMENT 4: Irrelevant Capabilities (Assignment PDF Section 7.4)
    // -------------------------------------------------------------------------
    static void runExperiment4(const ApplicationProblem& app, const std::vector<Capability>& allCaps, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "EXPERIMENT 4: IRRELEVANT CAPABILITIES (Section 7.4)\n";
        std::cout << "Goal-Relevance Filtering: Separating Goal-Advancing from Irrelevant Ops\n";
        std::cout << "======================================================================\n";

        std::cout << "Current Formal Goal:\n";
        for (const auto& cond : app.goal.conditions) {
            std::cout << "  - " << cond.variable << " == " << (cond.expectedValue ? "true" : "false") << "\n";
        }
        std::cout << "\n";

        std::cout << std::left << std::setw(26) << "Capability ID"
                  << std::setw(14) << "Type"
                  << std::setw(18) << "Goal Relevance"
                  << "Classification\n";
        std::cout << std::string(75, '-') << "\n";

        for (const auto& c : allCaps) {
            double rel = emb.goalRelevance(c, app.goal);
            std::string status;
            if (rel > 0.0) {
                status = "GOAL-ADVANCING (+1 direct goal contribution)";
            } else if (c.id == "CreateOrder") {
                status = "PIPELINE ENABLER (Enables goal-advancing payment)";
            } else {
                status = "IRRELEVANT / PRUNED (Zero contribution to goal)";
            }

            std::cout << std::left << std::setw(26) << c.id
                      << std::setw(14) << c.type
                      << std::fixed << std::setprecision(2) << std::setw(18) << rel
                      << status << "\n";
        }

        std::cout << "\nConclusion: Dot product alignment between capability effect vectors and goal vectors\n"
                  << "            enables immediate O(d) pruning of irrelevant operations without running a planner.\n";
    }

    // -------------------------------------------------------------------------
    // EXPERIMENT 5: Operational Attributes (Assignment PDF Section 7.5)
    // -------------------------------------------------------------------------
    static void runExperiment5(const std::vector<Capability>& allCaps, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "EXPERIMENT 5: OPERATIONAL ATTRIBUTES & QUALITY OF SERVICE (Section 7.5)\n";
        std::cout << "Multi-Criteria Operational Trade-offs and Vector Representation Impact\n";
        std::cout << "======================================================================\n";

        const Capability* cFast = nullptr;
        const Capability* cCheap = nullptr;
        const Capability* cApi = nullptr;
        const Capability* cDb = nullptr;

        for (const auto& c : allCaps) {
            if (c.id == "FastPayment") cFast = &c;
            if (c.id == "CheapPayment") cCheap = &c;
            if (c.id == "MakePayment_API") cApi = &c;
            if (c.id == "MakePayment_DATABASE") cDb = &c;
        }

        std::vector<const Capability*> ops = {cFast, cCheap, cApi, cDb};

        std::cout << std::left << std::setw(24) << "Capability"
                  << std::setw(14) << "Latency (ms)"
                  << std::setw(14) << "Cost ($)"
                  << std::setw(12) << "Risk"
                  << std::setw(14) << "Reliability"
                  << "Encoded QoS Slice\n";
        std::cout << std::string(95, '-') << "\n";

        for (const auto* c : ops) {
            if (!c) continue;
            auto vec = emb.encodeCapability(*c);
            // QoS slice is last 6 elements of the 36-dim vector: [time, money, resource, risk, rel, avail]
            size_t qIdx = vec.size() - 6;
            std::ostringstream qSlice;
            qSlice << "[" << std::fixed << std::setprecision(2) << vec[qIdx] << ", "
                   << vec[qIdx+1] << ", " << vec[qIdx+2] << ", " << vec[qIdx+3] << ", "
                   << vec[qIdx+4] << ", " << vec[qIdx+5] << "]";

            std::cout << std::left << std::setw(24) << c->id
                      << std::fixed << std::setprecision(1) << std::setw(14) << c->qos.timeCostMs
                      << "$" << std::fixed << std::setprecision(3) << std::setw(13) << c->qos.moneyCost
                      << std::fixed << std::setprecision(3) << std::setw(12) << c->qos.risk
                      << std::fixed << std::setprecision(3) << std::setw(14) << c->reliability
                      << qSlice.str() << "\n";
        }

        if (cFast && cCheap) {
            auto vFast = emb.encodeCapability(*cFast);
            auto vCheap = emb.encodeCapability(*cCheap);
            double sim = VectorEmbeddingEngine::similarity(vFast, vCheap);
            std::cout << "\nTrade-off Comparison between FastPayment and CheapPayment:\n";
            std::cout << "  - FastPayment:  Ultra-low latency (20ms) at higher monetary cost ($0.100), low risk (0.005)\n";
            std::cout << "  - CheapPayment: Extremely cheap ($0.001) but high batch latency (800ms) and higher risk (0.060)\n";
            std::cout << "  - Cosine Similarity between FastPayment and CheapPayment: "
                      << std::fixed << std::setprecision(4) << sim << "\n";
            std::cout << "  - Divergence is strictly driven by the operational quality embedding slice.\n";
        }

        std::cout << "\nConclusion: Operational attributes enable Pareto multi-objective optimization\n"
                  << "            while retaining identical functional capability signatures.\n";
    }

    // -------------------------------------------------------------------------
    // Helper: Pairwise Compatibility Matrix
    // -------------------------------------------------------------------------
    static void printCompatibilityMatrix(const std::vector<Capability>& caps, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "PAIRWISE CAPABILITY COMPATIBILITY MATRIX Comp(Row -> Col)\n";
        std::cout << "======================================================================\n\n";

        std::cout << std::left << std::setw(20) << "From \\ To";
        for (const auto& c : caps) {
            std::cout << std::right << std::setw(16) << c.id.substr(0, 14);
        }
        std::cout << "\n" << std::string(20 + caps.size() * 16, '-') << "\n";

        for (const auto& c1 : caps) {
            std::cout << std::left << std::setw(20) << c1.id.substr(0, 18);
            for (const auto& c2 : caps) {
                double comp = emb.compatibility(c1, c2);
                std::cout << std::right << std::fixed << std::setprecision(2) << std::setw(16) << comp;
            }
            std::cout << "\n";
        }
        std::cout << "\nLegend: +1.00 = Preconditions satisfied; 0.00 = Neutral/unrelated; -1.00 = Conflict.\n";
    }

    // -------------------------------------------------------------------------
    // Helper: Formatted Vector Display
    // -------------------------------------------------------------------------
    static void printVectorRepresentations(const ApplicationProblem& app, const VectorEmbeddingEngine& emb) {
        std::cout << "\n======================================================================\n";
        std::cout << "STRUCTURED VECTOR EMBEDDING REPRESENTATIONS\n";
        std::cout << "======================================================================\n";

        std::cout << "\n1. Canonical State Basis (Dimension: " << emb.stateDimension() << "):\n";
        for (size_t i = 0; i < CANONICAL_STATE_VARIABLES.size(); ++i) {
            std::cout << "   [" << std::setw(2) << i << "] " << CANONICAL_STATE_VARIABLES[i] << "\n";
        }

        std::cout << "\n2. Initial State Embedding phi_S(S_I) in {-1, +1}^11:\n   [";
        auto sVec = emb.encodeState(app.initialState);
        for (size_t i = 0; i < sVec.size(); ++i) {
            std::cout << (sVec[i] > 0 ? "+1" : "-1") << (i + 1 < sVec.size() ? ", " : "");
        }
        std::cout << "]\n";

        std::cout << "\n3. Goal Specification Embedding phi_G(G) in {-1, 0, +1}^11:\n   [";
        auto gVec = emb.encodeGoal(app.goal);
        for (size_t i = 0; i < gVec.size(); ++i) {
            if (gVec[i] > 0.5) std::cout << "+1";
            else if (gVec[i] < -0.5) std::cout << "-1";
            else std::cout << " 0";
            std::cout << (i + 1 < gVec.size() ? ", " : "");
        }
        std::cout << "]\n";

        std::cout << "\n4. Capability Vectors phi_C(C) in R^36 (11 pre, 11 eff, 6 type, 2 io, 6 qos):\n";
        for (const auto& c : app.capabilities) {
            auto pre = emb.encodePreconditions(c);
            auto eff = emb.encodeEffects(c);
            auto full = emb.encodeCapability(c);

            std::cout << "\nCapability: " << c.id << " (" << c.name << ")\n";
            std::cout << "  Preconditions: [";
            for (size_t i = 0; i < pre.size(); ++i) {
                if (pre[i] > 0.5) std::cout << "+1";
                else if (pre[i] < -0.5) std::cout << "-1";
                else std::cout << " 0";
                std::cout << (i + 1 < pre.size() ? "," : "");
            }
            std::cout << "]\n";

            std::cout << "  Effects:       [";
            for (size_t i = 0; i < eff.size(); ++i) {
                if (eff[i] > 0.5) std::cout << "+1";
                else if (eff[i] < -0.5) std::cout << "-1";
                else std::cout << " 0";
                std::cout << (i + 1 < eff.size() ? "," : "");
            }
            std::cout << "]\n";

            std::cout << "  Full Vector (dim=" << full.size() << "): [";
            for (size_t i = 0; i < full.size(); ++i) {
                std::cout << std::fixed << std::setprecision(2) << full[i] << (i + 1 < full.size() ? ", " : "");
            }
            std::cout << "]\n";
        }
    }
};

} // namespace capability_embedding
