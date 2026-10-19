class State:
    def __init__(self, variables):
        self.variables = variables

    def get(self, key):
        return self.variables.get(key)

    def set(self, key, value):
        self.variables[key] = value

    def __repr__(self):
        return f"State({self.variables})"