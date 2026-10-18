# Assignment Alignment

| Specification requirement | Implementation |
|---|---|
| Formal A=(S,C,SI,G,R,K) | Problem/State/Goal/Capability structures in types.hpp and JSON dataset |
| 11-part capability model | Capability stores T,I,O,P,E,K,R,Q,Rel,A,M |
| encode(state) | EmbeddingEngine::encode(State) |
| encode(goal) | EmbeddingEngine::encode(Goal) |
| encode(capability) | EmbeddingEngine::encode(Capability) |
| compose(capabilities) | EmbeddingEngine::compose |
| similarity(x,y) | EmbeddingEngine::similarity |
| Precondition-effect compatibility | EmbeddingEngine::compatibility |
| Input-output compatibility | EmbeddingEngine::ioCompatibility |
| Composition experiment | CreateOrder -> MakePayment -> SendNotification |
| Alternative implementations | CreateOrder / _DB / _GUI |
| Irrelevant capabilities | AddToCart / UpdateProfile etc. |
| Operational attributes | cost, reliability, availability, risk, resource |
| Deliverables 1-4 | Four deliverable files + DOCX |
| Planner algorithms excluded | No BFS/DFS/A*/D* Lite/LPA*/replanning code |
