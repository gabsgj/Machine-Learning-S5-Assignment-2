#pragma once
#include "embedding.hpp"
#include <iostream>
#include <iomanip>
#include <string>
namespace capability {
class Experiments{
    static const Capability* f(const Problem&p,const std::string&id){for(auto&c:p.capabilities)if(c.id==id)return &c;return nullptr;}
public:
 static void run(const Problem&p,const EmbeddingEngine&e){
  auto c1=f(p,"CreateOrder"),c2=f(p,"MakePayment"),c3=f(p,"CancelCart"),c4=f(p,"SendNotification");
  auto api=f(p,"CreateOrder"),db=f(p,"CreateOrder_DB"),gui=f(p,"CreateOrder_GUI");
  std::cout<<"\n=== EXPERIMENT 1: CAPABILITY COMPATIBILITY ===\n";
  std::cout<<"CreateOrder -> MakePayment = "<<std::fixed<<std::setprecision(2)<<e.compatibility(*c1,*c2)<<" (compatible)\n";
  std::cout<<"CreateOrder -> CancelCart = "<<e.compatibility(*c1,*c3)<<" (incompatible)\n";
  std::cout<<"Input/output CreateOrder -> MakePayment = "<<e.ioCompatibility(*c1,*c2)<<"\n";

  auto c12=e.compose(*c1,*c2), c123=e.compose(c12,*c4);
  auto vc=e.encode(c123);
  std::cout<<"\n=== EXPERIMENT 2: CAPABILITY COMPOSITION ===\n";
  std::cout<<"Composite = "<<c123.id<<"\nDimension = "<<vc.size()<<"\n";
  std::cout<<"Time = "<<c123.qos.timeMs<<" ms, Cost = $"<<c123.qos.money<<", Reliability = "<<c123.reliability<<"\n";
  std::cout<<"Similarity with CreateOrder = "<<e.similarity(vc,e.encode(*c1))<<"\n";
  std::cout<<"Similarity with MakePayment = "<<e.similarity(vc,e.encode(*c2))<<"\n";
  std::cout<<"Similarity with SendNotification = "<<e.similarity(vc,e.encode(*c4))<<"\n";

  std::cout<<"\n=== EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS ===\n";
  std::cout<<"Effect similarity API/DB = "<<e.similarity(e.eff(*api),e.eff(*db))<<"\n";
  std::cout<<"Effect similarity API/GUI = "<<e.similarity(e.eff(*api),e.eff(*gui))<<"\n";
  std::cout<<"Full capability similarity API/DB = "<<e.similarity(e.encode(*api),e.encode(*db))<<"\n";
  std::cout<<"Full capability similarity API/GUI = "<<e.similarity(e.encode(*api),e.encode(*gui))<<"\n";
  std::cout<<"CreateOrder -> DB compatibility = "<<e.compatibility(*api,*db)<<" (alternative implementations are not sequential stages)\n";

  std::cout<<"\n=== EXPERIMENT 4: IRRELEVANT CAPABILITIES / GOAL RELEVANCE ===\n";
  auto g=e.encodeGoal(p.goal);
  for(auto&c:p.capabilities)std::cout<<std::left<<std::setw(24)<<c.id<<" effect-goal cosine = "<<std::fixed<<std::setprecision(4)<<e.similarity(e.eff(c),g)<<"\n";

  std::cout<<"\n=== EXPERIMENT 5: OPERATIONAL ATTRIBUTES ===\n";
  std::cout<<std::left<<std::setw(24)<<"Capability"<<std::setw(10)<<"ms"<<std::setw(10)<<"cost"<<std::setw(12)<<"reliability"<<std::setw(10)<<"avail"<<"risk\n";
  for(auto&c:p.capabilities)std::cout<<std::left<<std::setw(24)<<c.id<<std::setw(10)<<c.qos.timeMs<<std::setw(10)<<c.qos.money<<std::setw(12)<<c.reliability<<std::setw(10)<<c.availability<<c.qos.risk<<"\n";
  std::cout<<"\nSensitivity test using CreateOrder variants:\n";
  const Capability* base=f(p,"CreateOrder");
  if(base){
    for(const auto&name: {std::string("higher_cost"),std::string("lower_reliability"),std::string("unavailable"),std::string("higher_risk")}){
      Capability v=*base;
      if(name=="higher_cost") v.qos.money=0.040;
      if(name=="lower_reliability") v.reliability=0.800;
      if(name=="unavailable") v.availability=0.0;
      if(name=="higher_risk") v.qos.risk=0.500;
      std::cout<<std::setw(22)<<name<<" cosine-to-baseline="<<e.similarity(e.encode(*base),e.encode(v))<<"\n";
    }
  }
  std::cout<<"Functional precondition/effect blocks are unchanged in these variants; only operational fields are perturbed.\n";
 }
};
}
