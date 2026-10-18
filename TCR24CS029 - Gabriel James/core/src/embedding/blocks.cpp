#include "careweave/embedding/blocks.hpp"

#include <algorithm>

namespace careweave {
namespace embedding {

std::vector<BlockSpec> Blocks::capabilityBlocks() {
  return {{"type", kTypeOffset, kTypeDim},
          {"mechanism", kMechOffset, kMechDim},
          {"inputs", kInOffset, kInDim},
          {"outputs", kOutOffset, kOutDim},
          {"preconditions", kPreOffset, kPreDim},
          {"effects", kEffOffset, kEffDim},
          {"delta", kDeltaOffset, kDeltaDim},
          {"resources", kResOffset, kResDim},
          {"quality", kQOffset, kQDim},
          {"reliability", kRelOffset, kRelDim},
          {"availability", kAvailOffset, kAvailDim}};
}

int Blocks::capabilityBlockIndex(const std::string& name) {
  const std::vector<BlockSpec> blocks = capabilityBlocks();
  for (size_t i = 0; i < blocks.size(); ++i) {
    if (name == blocks[i].name) return static_cast<int>(i);
  }
  return -1;
}

bool Blocks::blocksComparable(const std::string& a, const std::string& b) {
  const auto width = [](const std::string& name) -> size_t {
    for (const auto& block : capabilityBlocks()) {
      if (name == block.name) return block.width;
    }
    if (name == "state_core" || name == "goal_core") return kSharedCoreDim;
    if (name == "state" || name == "goal") return kStateDim;
    if (name == "capability") return kCapabilityDim;
    return 0;
  };
  const size_t wa = width(a), wb = width(b);
  if (wa == 0 || wb == 0) return false;
  // Condition blocks share the condition space, IO blocks share the IO space, and equal width
  // blocks of the same family compare directly.
  const bool aCond = (a == "preconditions" || a == "effects" || a == "state_core" ||
                      a == "goal_core");
  const bool bCond = (b == "preconditions" || b == "effects" || b == "state_core" ||
                      b == "goal_core");
  if (aCond || bCond) return aCond && bCond;
  const bool aIo = (a == "inputs" || a == "outputs");
  const bool bIo = (b == "inputs" || b == "outputs");
  if (aIo || bIo) return aIo && bIo;
  return wa == wb;
}

}  // namespace embedding
}  // namespace careweave
