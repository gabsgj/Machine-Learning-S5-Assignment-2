#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <cstdint>

using namespace std;

// Assignment 2: Vector Embedding for Capability Composition
// Standalone C++17 implementation using a deterministic structured embedding.

constexpr int DIM = 64;
constexpr int OP_BASE = 56; // 8 dimensions reserved for operational attributes.

struct State {
    map<string, string> values;
};

struct Goal {
    map<string, string> conditions;
};

struct Capability {
    string name;
    string type;       // API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE
    string mechanism;
    vector<string> inputs;
    vector<string> outputs;
    vector<string> preconditions;
    vector<string> effects;
    vector<string> constraints;
    vector<string> resources;
    double time_ms = 0.0;
    double resource_cost = 0.0;
    double money_cost = 0.0;
    double risk = 0.0;
    double reliability = 1.0;
    bool available = true;
};

using Vec = vector<double>;

string lowerCopy(string s) {
    transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return (char)tolower(c); });
    return s;
}

uint64_t fnv1a(const string& s) {
    uint64_t h = 1469598103934665603ULL;
    for (unsigned char c : s) {
        h ^= c;
        h *= 1099511628211ULL;
    }
    return h;
}

void addHashed(Vec& v, const string& namespaceName, const string& token, double weight) {
    string key = namespaceName + "|" + lowerCopy(token);
    uint64_t h = fnv1a(key);
    int bucket = static_cast<int>(h % 32ULL);       // dimensions 0..31
    int sign = ((h >> 32) & 1ULL) ? 1 : -1;
    v[bucket] += sign * weight;
}

void addHashedSecond(Vec& v, const string& namespaceName, const string& token, double weight) {
    string key = namespaceName + "|" + lowerCopy(token);
    uint64_t h = fnv1a(key + "#2");
    int bucket = 32 + static_cast<int>(h % 24ULL);  // dimensions 32..55
    int sign = ((h >> 33) & 1ULL) ? 1 : -1;
    v[bucket] += sign * weight;
}

void normalize(Vec& v) {
    double n = 0.0;
    for (double x : v) n += x * x;
    n = sqrt(n);
    if (n > 1e-12) for (double& x : v) x /= n;
}

Vec encodeState(const State& s) {
    Vec v(DIM, 0.0);
    for (const auto& [k, val] : s.values) {
        addHashed(v, "condition.var", k, 1.0);
        addHashed(v, "condition.value", k + "=" + val, 1.2);
    }
    normalize(v);
    return v;
}

Vec encodeGoal(const Goal& g) {
    Vec v(DIM, 0.0);
    for (const auto& [k, val] : g.conditions) {
        addHashed(v, "condition.var", k, 1.1);
        addHashed(v, "condition.value", k + "=" + val, 1.5);
    }
    normalize(v);
    return v;
}

Vec encodeCapability(const Capability& c) {
    Vec v(DIM, 0.0);

    addHashed(v, "cap.type", c.type, 1.6);
    addHashed(v, "cap.mechanism", c.mechanism, 1.1);

    for (const auto& x : c.inputs)       addHashed(v, "cap.input", x, 0.9);
    for (const auto& x : c.outputs)      addHashed(v, "cap.output", x, 1.0);
    for (const auto& x : c.preconditions) addHashed(v, "cap.pre", x, 1.3);
    for (const auto& x : c.effects)      addHashed(v, "cap.effect", x, 1.5);
    for (const auto& x : c.constraints)  addHashedSecond(v, "cap.constraint", x, 0.8);
    for (const auto& x : c.resources)    addHashedSecond(v, "cap.resource", x, 0.8);

    // Operational dimensions are explicit, so they remain interpretable.
    v[OP_BASE + 0] = min(c.time_ms / 1000.0, 1.0);       // execution time, 0..1 after 1s
    v[OP_BASE + 1] = min(c.resource_cost / 10.0, 1.0);   // resource cost
    v[OP_BASE + 2] = min(c.money_cost / 1.0, 1.0);       // money cost
    v[OP_BASE + 3] = min(max(c.risk, 0.0), 1.0);         // risk
    v[OP_BASE + 4] = min(max(c.reliability, 0.0), 1.0);  // reliability
    v[OP_BASE + 5] = c.available ? 1.0 : 0.0;            // availability
    v[OP_BASE + 6] = min(c.inputs.size() / 5.0, 1.0);    // input count
    v[OP_BASE + 7] = min(c.outputs.size() / 5.0, 1.0);   // output count

    normalize(v);
    return v;
}

// Cosine similarity for any two encoded entities.
double similarity(const Vec& a, const Vec& b) {
    double dot = inner_product(a.begin(), a.end(), b.begin(), 0.0);
    double na = sqrt(inner_product(a.begin(), a.end(), a.begin(), 0.0));
    double nb = sqrt(inner_product(b.begin(), b.end(), b.begin(), 0.0));
    if (na < 1e-12 || nb < 1e-12) return 0.0;
    return dot / (na * nb);
}

set<string> toSet(const vector<string>& x) { return set<string>(x.begin(), x.end()); }

// Directional functional compatibility: effects/outputs of A should satisfy
// preconditions/inputs of B. This complements cosine similarity because
// functional similarity and composability are intentionally different.
double compatibility(const Capability& a, const Capability& b) {
    set<string> aEffects = toSet(a.effects);
    set<string> aOutputs = toSet(a.outputs);
    set<string> bPre = toSet(b.preconditions);
    set<string> bInputs = toSet(b.inputs);

    int preMatched = 0;
    for (const auto& x : bPre) if (aEffects.count(x)) preMatched++;
    double preScore = bPre.empty() ? 1.0 : static_cast<double>(preMatched) / bPre.size();

    int inputMatched = 0;
    for (const auto& x : bInputs) if (aOutputs.count(x)) inputMatched++;
    // Inputs may also be supplied externally. Therefore missing input/output
    // overlap is not automatically a composition failure.
    double ioScore = bInputs.empty() ? 1.0 : static_cast<double>(inputMatched) / bInputs.size();

    return 0.7 * preScore + 0.3 * ioScore;
}

bool canCompose(const Capability& a, const Capability& b) {
    set<string> aEffects = toSet(a.effects);
    for (const auto& pre : b.preconditions) {
        if (!aEffects.count(pre)) return false;
    }
    return true;
}

// Goal relevance: fraction of goal conditions directly produced by a capability.
double goalRelevance(const Capability& c, const Goal& g) {
    if (g.conditions.empty()) return 0.0;
    set<string> effects = toSet(c.effects);
    int hit = 0;
    for (const auto& [k, val] : g.conditions) {
        if (effects.count(k + "=" + val) || effects.count(k + "=" + lowerCopy(val))) hit++;
    }
    return static_cast<double>(hit) / g.conditions.size();
}

Capability composeCapabilities(const vector<Capability>& chain) {
    Capability out;
    out.name = "Composite";
    out.type = "COMPOSITE";
    out.mechanism = "SEQUENTIAL_COMPOSITION";

    for (size_t i = 0; i < chain.size(); ++i) {
        const Capability& c = chain[i];
        if (i == 0) out.preconditions = c.preconditions;
        out.effects.insert(out.effects.end(), c.effects.begin(), c.effects.end());
        out.outputs.insert(out.outputs.end(), c.outputs.begin(), c.outputs.end());
        out.resources.insert(out.resources.end(), c.resources.begin(), c.resources.end());
        out.constraints.insert(out.constraints.end(), c.constraints.begin(), c.constraints.end());
        out.time_ms += c.time_ms;
        out.resource_cost += c.resource_cost;
        out.money_cost += c.money_cost;
        out.risk = 1.0 - (1.0 - out.risk) * (1.0 - c.risk);
        out.reliability *= c.reliability;
        out.available = out.available && c.available;
    }
    // Remove duplicate outputs/resources/constraints.
    auto unique = [](vector<string>& xs) {
        set<string> s(xs.begin(), xs.end());
        xs.assign(s.begin(), s.end());
    };
    unique(out.effects); unique(out.outputs); unique(out.resources); unique(out.constraints);
    return out;
}

// Order-aware composite embedding. The positional weighting distinguishes
// sequences while retaining information from every atomic capability.
Vec encodeComposite(const vector<Capability>& chain) {
    Vec v(DIM, 0.0);
    if (chain.empty()) return v;
    double weightSum = 0.0;
    for (size_t i = 0; i < chain.size(); ++i) {
        Vec x = encodeCapability(chain[i]);
        double w = 1.0 / static_cast<double>(i + 1);
        for (int d = 0; d < DIM; ++d) v[d] += w * x[d];
        addHashed(v, "composition.step", chain[i].name + ":" + to_string(i + 1), 0.5);
        weightSum += w;
    }
    if (weightSum > 0) for (double& x : v) x /= weightSum;
    normalize(v);
    return v;
}

void printVector(const Vec& v, const string& label, int n = 10) {
    cout << label << " [";
    for (int i = 0; i < min(n, (int)v.size()); ++i) {
        if (i) cout << ", ";
        cout << fixed << setprecision(3) << v[i];
    }
    cout << ", ...] (dim=" << v.size() << ")\n";
}

Capability makeCapability(string name, string type, string mechanism,
                          vector<string> in, vector<string> out,
                          vector<string> pre, vector<string> eff,
                          vector<string> con, vector<string> res,
                          double time, double rcost, double mcost,
                          double risk, double rel, bool avail = true) {
    Capability c;
    c.name = move(name); c.type = move(type); c.mechanism = move(mechanism);
    c.inputs = move(in); c.outputs = move(out); c.preconditions = move(pre);
    c.effects = move(eff); c.constraints = move(con); c.resources = move(res);
    c.time_ms = time; c.resource_cost = rcost; c.money_cost = mcost;
    c.risk = risk; c.reliability = rel; c.available = avail;
    return c;
}

int main() {
    cout << "=== Vector Embedding for Capability Composition ===\n";
    cout << "Structured Capability Embedding (SCE), dimension = " << DIM << "\n\n";

    State initial{{
        {"User.authenticated", "true"},
        {"User.role", "CUSTOMER"},
        {"Cart.exists", "true"},
        {"Cart.item_count", "3"},
        {"Order.exists", "false"},
        {"Payment.status", "NOT_STARTED"},
        {"Inventory.available", "true"},
        {"Notification.sent", "false"}
    }};

    Goal goal{{
        {"Order.exists", "true"},
        {"Payment.status", "SUCCESS"},
        {"Notification.sent", "true"}
    }};

    Capability createOrder = makeCapability(
        "CreateOrder", "API", "POST /orders",
        {"cart_id"}, {"order_id"},
        {"Cart.exists=true", "Cart.item_count>0", "Inventory.available=true"},
        {"Order.exists=true", "Order.status=CREATED"},
        {"quantity>0"}, {"Database", "Network"},
        100, 2, 0.01, 0.05, 0.99);

    Capability makePayment = makeCapability(
        "MakePayment", "SERVICE", "PaymentGateway.charge",
        {"order_id", "payment_amount"}, {"payment_id", "Payment.status"},
        {"Order.exists=true"},
        {"Payment.status=SUCCESS"},
        {"payment_amount<=transaction_limit"}, {"Payment gateway", "Network"},
        180, 3, 0.10, 0.08, 0.98);

    Capability cancelCart = makeCapability(
        "CancelCart", "FUNCTION", "cancel_cart()",
        {"cart_id"}, {"cancel_status"},
        {"Order.exists=false"},
        {"Cart.cancelled=true"},
        {"quantity>0"}, {"Database"},
        80, 1, 0.00, 0.03, 0.995);

    Capability sendNotification = makeCapability(
        "SendNotification", "EVENT", "OrderPaid -> SendNotification",
        {"order_id"}, {"notification_id"},
        {"Payment.status=SUCCESS"},
        {"Notification.sent=true"},
        {}, {"External service", "Network"},
        120, 2, 0.02, 0.04, 0.97);

    Capability createOrderDB = makeCapability(
        "CreateOrderDB", "DATABASE", "INSERT orders",
        {"cart_id"}, {"order_id"},
        {"Cart.exists=true", "Cart.item_count>0", "Inventory.available=true"},
        {"Order.exists=true", "Order.status=CREATED"},
        {"quantity>0"}, {"Database"},
        60, 1, 0.005, 0.04, 0.995);

    Capability createOrderGUI = makeCapability(
        "CreateOrderGUI", "GUI", "CLICK submit_button",
        {"cart_id"}, {"order_id"},
        {"Cart.exists=true", "Cart.item_count>0", "Inventory.available=true"},
        {"Order.exists=true", "Order.status=CREATED"},
        {"quantity>0"}, {"Authentication token", "Network"},
        350, 4, 0.00, 0.12, 0.94);

    Capability updateProfile = makeCapability(
        "UpdateProfile", "DATABASE", "UPDATE users",
        {"user_id"}, {"profile_status"},
        {"User.authenticated=true"},
        {"User.profile_updated=true"},
        {}, {"Database"},
        70, 1, 0.00, 0.02, 0.995);

    Vec sVec = encodeState(initial);
    Vec gVec = encodeGoal(goal);
    Vec c1Vec = encodeCapability(createOrder);
    Vec c2Vec = encodeCapability(makePayment);
    Vec c3Vec = encodeCapability(cancelCart);

    printVector(sVec, "Initial state vector");
    printVector(gVec, "Goal vector");
    printVector(c1Vec, "CreateOrder vector");

    cout << "\n--- Experiment 1: Capability compatibility ---\n";
    cout << "CreateOrder -> MakePayment compatibility: " << fixed << setprecision(3)
         << compatibility(createOrder, makePayment) << " (" << (canCompose(createOrder, makePayment) ? "compatible" : "incompatible") << ")\n";
    cout << "CreateOrder -> CancelCart compatibility: " << compatibility(createOrder, cancelCart)
         << " (" << (canCompose(createOrder, cancelCart) ? "compatible" : "incompatible") << ")\n";
    cout << "CreateOrder cosine vs MakePayment: " << similarity(c1Vec, c2Vec) << "\n";
    cout << "CreateOrder cosine vs CancelCart: " << similarity(c1Vec, c3Vec) << "\n";

    cout << "\n--- Experiment 2: Three-step composition ---\n";
    vector<Capability> chain{createOrder, makePayment, sendNotification};
    Capability composite = composeCapabilities(chain);
    Vec compVec = encodeComposite(chain);
    printVector(compVec, "CompletePurchase composite vector");
    cout << "Chain validity: "
         << (canCompose(createOrder, makePayment) && canCompose(makePayment, sendNotification) ? "VALID" : "INVALID") << "\n";
    cout << "Composite similarity to CreateOrder: " << similarity(compVec, c1Vec) << "\n";
    cout << "Composite similarity to MakePayment: " << similarity(compVec, c2Vec) << "\n";
    cout << "Composite similarity to SendNotification: " << similarity(compVec, encodeCapability(sendNotification)) << "\n";
    cout << "Composite goal relevance: " << goalRelevance(composite, goal) << "\n";

    cout << "\n--- Experiment 3: Alternative implementations ---\n";
    Vec dbVec = encodeCapability(createOrderDB);
    Vec guiVec = encodeCapability(createOrderGUI);
    cout << "API CreateOrder vs DB CreateOrder cosine: " << similarity(c1Vec, dbVec) << "\n";
    cout << "API CreateOrder vs GUI CreateOrder cosine: " << similarity(c1Vec, guiVec) << "\n";
    cout << "API CreateOrder -> MakePayment compatibility: " << compatibility(createOrder, makePayment) << "\n";
    cout << "DB CreateOrder -> MakePayment compatibility: " << compatibility(createOrderDB, makePayment) << "\n";
    cout << "GUI CreateOrder -> MakePayment compatibility: " << compatibility(createOrderGUI, makePayment) << "\n";

    cout << "\n--- Experiment 4: Irrelevant capability ---\n";
    Vec profileVec = encodeCapability(updateProfile);
    cout << "CreateOrder goal relevance: " << goalRelevance(createOrder, goal) << "\n";
    cout << "UpdateProfile goal relevance: " << goalRelevance(updateProfile, goal) << "\n";
    cout << "CreateOrder vs UpdateProfile cosine: " << similarity(c1Vec, profileVec) << "\n";

    cout << "\n--- Experiment 5: Operational attributes ---\n";
    cout << "CreateOrder reliability=" << createOrder.reliability << ", risk=" << createOrder.risk
         << ", available=" << (createOrder.available ? 1 : 0) << ", time_ms=" << createOrder.time_ms << "\n";
    cout << "CreateOrderGUI reliability=" << createOrderGUI.reliability << ", risk=" << createOrderGUI.risk
         << ", available=" << (createOrderGUI.available ? 1 : 0) << ", time_ms=" << createOrderGUI.time_ms << "\n";
    cout << "API vs GUI cosine with operational attributes: " << similarity(c1Vec, guiVec) << "\n";
    Capability degraded = createOrder;
    degraded.name = "CreateOrder_Degraded";
    degraded.time_ms = 500;
    degraded.risk = 0.50;
    degraded.reliability = 0.70;
    degraded.available = false;
    cout << "CreateOrder vs degraded operational profile cosine: "
         << similarity(c1Vec, encodeCapability(degraded)) << "\n";

    cout << "\n--- Experiment 6: State/goal similarity ---\n";
    cout << "Initial state vs goal cosine: " << similarity(sVec, gVec) << "\n";

    cout << "\n--- Experiment 7: Determinism / consistency ---\n";
    cout << "Repeated CreateOrder encoding cosine: "
         << similarity(c1Vec, encodeCapability(createOrder)) << " (expected 1.000)\n";

    cout << "\n=== Demonstration complete ===\n";
    return 0;
}
