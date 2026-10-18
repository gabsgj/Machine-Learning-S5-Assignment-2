#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <variant>
#include <sstream>
#include <cmath>
#include <algorithm>

namespace capability {
using Value = std::variant<bool,double,std::string>;
inline bool isNum(const Value& v){ return std::holds_alternative<double>(v); }
inline bool valueEqual(const Value& a,const Value& b){
    if(a.index()!=b.index()) return false;
    if(std::holds_alternative<bool>(a)) return std::get<bool>(a)==std::get<bool>(b);
    if(std::holds_alternative<double>(a)) return std::abs(std::get<double>(a)-std::get<double>(b))<1e-9;
    return std::get<std::string>(a)==std::get<std::string>(b);
}
inline std::string valueString(const Value& v){
    if(std::holds_alternative<bool>(v)) return std::get<bool>(v)?"true":"false";
    if(std::holds_alternative<double>(v)){std::ostringstream o;o<<std::get<double>(v);return o.str();}
    return std::get<std::string>(v);
}
inline double bipolar(const Value& v){
    if(std::holds_alternative<bool>(v)) return std::get<bool>(v)?1.0:-1.0;
    if(std::holds_alternative<double>(v)) return std::tanh(std::get<double>(v)/10.0);
    return 0.0; // categorical values are represented by deterministic one-hot codes below
}
struct State{
    std::unordered_map<std::string,Value> vars;
    Value get(const std::string& k, Value d=0.0) const {auto it=vars.find(k);return it==vars.end()?d:it->second;}
};
struct Condition{
    std::string variable,op; Value expectedValue;
    bool evaluate(const State& s) const{
        Value actual=s.get(variable,0.0);
        if(op=="==") return valueEqual(actual,expectedValue);
        if(op=="!=") return !valueEqual(actual,expectedValue);
        if(std::holds_alternative<double>(actual)&&std::holds_alternative<double>(expectedValue)){
            double a=std::get<double>(actual),b=std::get<double>(expectedValue);
            if(op==">") return a>b;
            if(op==">=") return a>=b;
            if(op=="<") return a<b;
            if(op=="<=") return a<=b;
        }
        return false;
    }
};
struct Effect{std::string variable,op;Value value;void apply(State& s)const{if(op=="SET")s.vars[variable]=value;}};
struct Port{std::string name,type,domain;bool required=true;};
struct QoS{double timeMs=0,money=0,resource=0,risk=0;};
struct Goal{std::vector<Condition> conditions;bool satisfied(const State&s)const{for(auto&c:conditions)if(!c.evaluate(s))return false;return true;}};
struct Capability{
    std::string id,name,description,type="SERVICE",mechanism;
    std::vector<Port> inputs,outputs;std::vector<Condition> preconditions,effects_as_conditions,constraints;std::vector<Effect> effects;
    std::vector<std::string> resources;QoS qos;double reliability=.99,availability=1.0;
    bool applicable(const State&s)const{if(availability<=0)return false;for(auto&p:preconditions)if(!p.evaluate(s))return false;for(auto&k:constraints)if(!k.evaluate(s))return false;return true;}
    State apply(const State&s)const{State n=s;for(auto&e:effects)e.apply(n);return n;}
};
struct Problem{std::string name,domain,description;State initial;Goal goal;std::vector<Condition> globalConstraints;std::vector<std::string> resources;std::vector<Capability> capabilities;};
}
