from igibson.object_states.object_state_base import AbsoluteObjectState
from igibson.object_states.utils import clear_cached_states
from igibson.objects.object_base import Object
from igibson.object_states.factory import (
    prepare_object_states,
    get_state_name,
    get_state_from_name,
)


class StatefulObject(Object):
    """
    Stateful Base Object class
    """

    def __init__(self):
        super(StatefulObject, self).__init__()
        self.abilities = {}
        prepare_object_states(self, online=True)

    def dump_state(self):
        return {
            get_state_name(state_type): state_instance.dump()
            for state_type, state_instance in self.states.items()
            if issubclass(state_type, AbsoluteObjectState)
        }

    def load_state(self, dump):
        for state_type, state_instance in self.states.items():
            if issubclass(state_type, AbsoluteObjectState):
                state_instance.load(dump[get_state_name(state_type)])

    def set_position(self, pos):
        super(StatefulObject, self).set_position(pos)
        clear_cached_states(self)

    def set_orientation(self, orn):
        super(StatefulObject, self).set_orientation(orn)
        clear_cached_states(self)

    def set_position_orientation(self, pos, orn):
        super(StatefulObject, self).set_position_orientation(pos, orn)
        clear_cached_states(self)

    def set_base_link_position_orientation(self, pos, orn):
        super(StatefulObject, self).set_base_link_position_orientation(pos, orn)
        clear_cached_states(self)
