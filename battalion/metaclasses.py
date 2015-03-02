class State(object):

    """
    Model that acts as a container class for state attributes for a larger
    class. It stuffs any kwarg it gets in it's init as an attribute of itself.

    """

    def __init__(self, **kwargs):
        self._merge(kwargs)

    def _merge(self, dict_obj):
        for key in dict_obj.keys():
            setattr(self, key, dict_obj[key])


class StateMixin(object):

    """
    Mixin that provides the State class support to add settings to instance
    objects. State settings cannot start with a _.

    """

    def __init__(self, *args, **kwargs):
        # Get a List of all the Classes we in our MRO, find any attribute named
        #     State on them, and then merge them together in order of MRO
        states = reversed([x.State for x in self.__class__.mro()
                          if hasattr(x, "State")])
        final_state = {}

        # Merge the State classes into one dict
        for state in states:
            final_state.update(dict([x for x in state.__dict__.items()
                                    if not x[0].startswith("_")]))

        # Update the final state with any kwargs passed in
        for key in final_state.keys():
            if key in kwargs:
                final_state[key] = kwargs.pop(key)

        self._state = State(**final_state)

        super(StateMixin, self).__init__()


import six

class A(StateMixin):
    class State:
        Var1 = "Hello"
        Var2 = "World"

class B(A):
    class State:
        Var2 = "Kyle"
        
class C(B):
    class State:
        Var1 = "Goodbye"

a = A()
b = B()
c = C()

print a._state.Var1, a._state.Var2
print b._state.Var1, b._state.Var2
print c._state.Var1, c._state.Var2