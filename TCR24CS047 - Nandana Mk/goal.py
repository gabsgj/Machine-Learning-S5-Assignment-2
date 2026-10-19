class Goal:
    def __init__(self, conditions):
        self.conditions = conditions

    def is_satisfied(self, state):
        for key, value in self.conditions.items():
            if state.get(key) != value:
                return False
        return True

    def __repr__(self):
        return f"Goal({self.conditions})"