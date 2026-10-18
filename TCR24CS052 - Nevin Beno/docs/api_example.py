from src.embedding import StructuredEmbedder
from src.models import Capability, Condition
from src.compatibility import compatibility
from src.composition import compose_capabilities

# Minimal example:
create = Capability(
    name="CreateOrder",
    capability_type="API",
    effects=[Condition("Order.exists", "=", True)],
)

pay = Capability(
    name="MakePayment",
    capability_type="SERVICE",
    preconditions=[Condition("Order.exists", "=", True)],
    effects=[Condition("Payment.status", "=", "SUCCESS")],
)

embedder = StructuredEmbedder()

v1 = embedder.encode_capability(create)
v2 = embedder.encode_capability(pay)

print("Vector dimension:", len(v1))
print("Similarity:", embedder.similarity(v1, v2))
print("Compatibility:", compatibility(create, pay))

composite = compose_capabilities([create, pay], embedder)
print("Composite:", composite.name)
print("Composite reliability:", composite.reliability)
