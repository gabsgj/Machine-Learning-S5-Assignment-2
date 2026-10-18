#pragma once
#include "types.hpp"
#include <unordered_map>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>

namespace capability {
class EmbeddingEngine{
    std::unordered_map<std::string,size_t> varIndex,typeIndex,portIndex,resIndex,constraintIndex,mechanismIndex,valueIndex;
    std::vector<std::string> vars,types,ports,resources,constraints,mechanisms,values;
    static size_t add(std::unordered_map<std::string,size_t>&m,std::vector<std::string>&v,const std::string&s){auto it=m.find(s);if(it!=m.end())return it->second;size_t i=v.size();m[s]=i;v.push_back(s);return i;}
    static std::string portKey(const Port&p){return p.name+":"+p.type;}
    static std::string condKey(const Condition&c){return c.variable+c.op+valueString(c.expectedValue);}
    static std::string valueKey(const std::string&var,const Value&v){return var+"="+valueString(v);}
    double valueCode(const Value&v)const{
        if(std::holds_alternative<bool>(v))return std::get<bool>(v)?1.0:-1.0;
        if(std::holds_alternative<double>(v))return std::tanh(std::get<double>(v)/10.0);
        return 0.0;
    }
    static void setOne(std::vector<double>&v,size_t i,double x){if(i<v.size())v[i]=x;}
public:
    void initialize(const Problem&p){
        for(auto&[k,v]:p.initial.vars){add(varIndex,vars,k);if(std::holds_alternative<std::string>(v))add(valueIndex,values,valueKey(k,v));}
        for(auto&g:p.goal.conditions){add(varIndex,vars,g.variable);if(std::holds_alternative<std::string>(g.expectedValue))add(valueIndex,values,valueKey(g.variable,g.expectedValue));}
        for(auto&g:p.globalConstraints){add(varIndex,vars,g.variable);if(std::holds_alternative<std::string>(g.expectedValue))add(valueIndex,values,valueKey(g.variable,g.expectedValue));}
        for(auto&c:p.capabilities){add(typeIndex,types,c.type);add(mechanismIndex,mechanisms,c.mechanism);for(auto&x:c.inputs)add(portIndex,ports,portKey(x));for(auto&x:c.outputs)add(portIndex,ports,portKey(x));for(auto&x:c.preconditions){add(varIndex,vars,x.variable);if(std::holds_alternative<std::string>(x.expectedValue))add(valueIndex,values,valueKey(x.variable,x.expectedValue));}
            for(auto&x:c.effects){add(varIndex,vars,x.variable);if(std::holds_alternative<std::string>(x.value))add(valueIndex,values,valueKey(x.variable,x.value));}
            for(auto&x:c.constraints){add(varIndex,vars,x.variable);if(std::holds_alternative<std::string>(x.expectedValue))add(valueIndex,values,valueKey(x.variable,x.expectedValue));add(constraintIndex,constraints,condKey(x));}for(auto&r:c.resources)add(resIndex,resources,r);}
    }
    size_t stateDim()const{return vars.size()+values.size();}
    size_t capabilityDim()const{return stateDim()*2+types.size()+mechanisms.size()+ports.size()*2+constraints.size()+resources.size()+6;}
    std::vector<double> encodeState(const State&s)const{std::vector<double>v(stateDim(),0);for(size_t i=0;i<vars.size();++i){auto it=s.vars.find(vars[i]);if(it!=s.vars.end()){if(std::holds_alternative<std::string>(it->second)){auto vi=valueIndex.find(valueKey(vars[i],it->second));if(vi!=valueIndex.end())v[vars.size()+vi->second]=1.0;}else v[i]=valueCode(it->second);}}return v;}
    std::vector<double> encode(const State&s)const{return encodeState(s);}
    std::vector<double> encodeGoal(const Goal&g)const{std::vector<double>v(stateDim(),0);for(auto&c:g.conditions){auto it=varIndex.find(c.variable);if(it!=varIndex.end()){if(std::holds_alternative<std::string>(c.expectedValue)){auto vi=valueIndex.find(valueKey(c.variable,c.expectedValue));if(vi!=valueIndex.end())v[vars.size()+vi->second]=1.0;}else setOne(v,it->second,valueCode(c.expectedValue));}}return v;}
    std::vector<double> encode(const Goal&g)const{return encodeGoal(g);}
    std::vector<double> pre(const Capability&c)const{std::vector<double>v(stateDim(),0);for(auto&p:c.preconditions){auto it=varIndex.find(p.variable);if(it!=varIndex.end()){if(std::holds_alternative<std::string>(p.expectedValue)){auto vi=valueIndex.find(valueKey(p.variable,p.expectedValue));if(vi!=valueIndex.end())v[vars.size()+vi->second]=1.0;}else setOne(v,it->second,valueCode(p.expectedValue));}}return v;}
    std::vector<double> eff(const Capability&c)const{std::vector<double>v(stateDim(),0);for(auto&e:c.effects){auto it=varIndex.find(e.variable);if(it!=varIndex.end()){if(std::holds_alternative<std::string>(e.value)){auto vi=valueIndex.find(valueKey(e.variable,e.value));if(vi!=valueIndex.end())v[vars.size()+vi->second]=1.0;}else setOne(v,it->second,valueCode(e.value));}}return v;}
    std::vector<double> encodeCapability(const Capability&c)const{
        std::vector<double>v=pre(c),x=eff(c);v.insert(v.end(),x.begin(),x.end());
        std::vector<double>one(types.size(),0);auto ti=typeIndex.find(c.type);if(ti!=typeIndex.end())one[ti->second]=1;v.insert(v.end(),one.begin(),one.end());
        std::vector<double>mech(mechanisms.size(),0);auto mi=mechanismIndex.find(c.mechanism);if(mi!=mechanismIndex.end())mech[mi->second]=1;v.insert(v.end(),mech.begin(),mech.end());
        std::vector<double>pin(ports.size(),0),pout(ports.size(),0);for(auto&p:c.inputs){auto it=portIndex.find(portKey(p));if(it!=portIndex.end())pin[it->second]=p.required?1:.5;}for(auto&p:c.outputs){auto it=portIndex.find(portKey(p));if(it!=portIndex.end())pout[it->second]=1;}v.insert(v.end(),pin.begin(),pin.end());v.insert(v.end(),pout.begin(),pout.end());
        std::vector<double>cv(constraints.size(),0);for(auto&k:c.constraints){auto it=constraintIndex.find(condKey(k));if(it!=constraintIndex.end())cv[it->second]=1;}v.insert(v.end(),cv.begin(),cv.end());
        std::vector<double>rv(resources.size(),0);for(auto&r:c.resources){auto it=resIndex.find(r);if(it!=resIndex.end())rv[it->second]=1;}v.insert(v.end(),rv.begin(),rv.end());
        v.push_back(c.qos.timeMs/200.0);v.push_back(c.qos.money*10.0);v.push_back(c.qos.resource/5.0);v.push_back(c.qos.risk);v.push_back(c.reliability);v.push_back(c.availability);return v;
    }
    std::vector<double> encode(const Capability&c)const{return encodeCapability(c);}
    static double similarity(const std::vector<double>&a,const std::vector<double>&b){if(a.size()!=b.size()||a.empty())return 0;double d=0,n1=0,n2=0;for(size_t i=0;i<a.size();++i){d+=a[i]*b[i];n1+=a[i]*a[i];n2+=b[i]*b[i];}return(n1<1e-12||n2<1e-12)?0:d/(std::sqrt(n1)*std::sqrt(n2));}
    double compatibility(const Capability&c1,const Capability&c2)const{if(c2.preconditions.empty())return 1;double s=0;for(auto&p:c2.preconditions){bool found=false;for(auto&e:c1.effects)if(e.variable==p.variable){found=true;s+=valueEqual(e.value,p.expectedValue)?1:-1;break;}if(!found)s+=0;}return s/c2.preconditions.size();}
    double ioCompatibility(const Capability&c1,const Capability&c2)const{if(c2.inputs.empty())return 1;double m=0;for(auto&in:c2.inputs)for(auto&out:c1.outputs)if(in.name==out.name&&in.type==out.type){m++;break;}return m/c2.inputs.size();}
    Capability compose(const Capability&c1,const Capability&c2)const{
        Capability c;c.id=c1.id+"_THEN_"+c2.id;c.name="Composite: "+c1.name+" -> "+c2.name;c.description="C2 o C1";c.type="COMPOSITE";c.mechanism=c1.mechanism+" -> "+c2.mechanism;
        c.preconditions=c1.preconditions;for(auto&p:c2.preconditions){bool sat=false;for(auto&e:c1.effects)if(e.variable==p.variable&&valueEqual(e.value,p.expectedValue))sat=true;if(!sat)c.preconditions.push_back(p);}c.effects=c1.effects;for(auto&e2:c2.effects){bool ow=false;for(auto&e:c.effects)if(e.variable==e2.variable){e=e2;ow=true;break;}if(!ow)c.effects.push_back(e2);}c.inputs=c1.inputs;c.outputs=c2.outputs;
        c.qos.timeMs=c1.qos.timeMs+c2.qos.timeMs;c.qos.money=c1.qos.money+c2.qos.money;c.qos.resource=std::max(c1.qos.resource,c2.qos.resource);c.qos.risk=1-(1-c1.qos.risk)*(1-c2.qos.risk);c.reliability=c1.reliability*c2.reliability;c.availability=c1.availability*c2.availability;c.resources=c1.resources;for(auto&r:c2.resources)if(std::find(c.resources.begin(),c.resources.end(),r)==c.resources.end())c.resources.push_back(r);return c;
    }
};
}
