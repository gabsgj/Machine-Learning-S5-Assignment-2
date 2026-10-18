#ifndef STATE_H
#define STATE_H

#include <string>
#include <map>

using namespace std;

struct State {
    string id;
    map<string, double> values;

    State() {}

    State(string stateId) {
        id = stateId;
    }

    void setValue(string key, double value) {
        values[key] = value;
    }
};

#endif