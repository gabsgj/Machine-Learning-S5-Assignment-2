from models.capability import Capability


class Composer:

    @staticmethod
    def are_compatible(cap1, cap2):
        """
        Check whether cap1 can compose with cap2.
        """

        # Check effects satisfy preconditions
        for key, value in cap2.preconditions.items():

            if key not in cap1.effects:
                return False

            if cap1.effects[key] != value:
                return False

        return True

    @staticmethod
    def compose(cap1, cap2):

        if not Composer.are_compatible(cap1, cap2):
            return None

        composite = Capability(

            name=cap1.name + "_" + cap2.name,

            capability_type="COMPOSITE",

            inputs=cap1.inputs,

            outputs=cap2.outputs,

            preconditions=cap1.preconditions,

            effects=cap2.effects,

            resources=list(set(cap1.resources + cap2.resources)),

            constraints=cap1.constraints + cap2.constraints,

            cost={
                "time": cap1.cost.get("time", 0)
                        + cap2.cost.get("time", 0),

                "money": cap1.cost.get("money", 0)
                         + cap2.cost.get("money", 0)
            },

            reliability=cap1.reliability * cap2.reliability,

            availability=min(cap1.availability,
                             cap2.availability),

            mechanism="Composite Capability"

        )

        return composite