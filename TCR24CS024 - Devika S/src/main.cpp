#include "engine.hpp"
#include "embedding.hpp"
#include "experiments.hpp"
#include <iostream>
using namespace capability;
int main(int argc,char**argv){
 std::string path=argc>1?argv[1]:"ecommerce_capability_dataset.json";
 try{auto p=loadProblem(path);EmbeddingEngine e;e.initialize(p);std::cout<<"PCCST503 ASSIGNMENT 2 - VECTOR EMBEDDING FOR CAPABILITY COMPOSITION\n";std::cout<<"Problem: "<<p.name<<"\nState dimension: "<<e.stateDim()<<"\nCapability dimension: "<<e.capabilityDim()<<"\n";Experiments::run(p,e);}
 catch(const std::exception&ex){std::cerr<<"Error: "<<ex.what()<<"\n";return 1;}return 0;
}
