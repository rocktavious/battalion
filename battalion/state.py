import logging
from copy import deepcopy
from pyul.coreUtils import DotifyDict


LOG = logging.getLogger(__name__)


class StateMixin(object):
    """
    Mixin that provides static configuration settings to instance
    objects. State settings cannot start with a _.
    """

    def __init__(self, *args, **kwargs):
        # Get a List of all the Classes we in our MRO,
        # find any attribute named State on them,
        # and then merge them together in order of MRO
        states = reversed([x.State for x in self.__class__.mro()
                          if hasattr(x, "State")])
        final_state = DotifyDict()

        # Merge the State classes into one dict
        for s in states:
            data = [x for x in s.__dict__.items() if not x[0].startswith("_")]
            data = DotifyDict(deepcopy(dict(data)))
            final_state.update(data)

        # Update the final state with any kwargs passed in
        for key in final_state.keys():
            if key in kwargs:
                final_state[key] = kwargs.pop(key)

        LOG.info("Setting {0} state to:\n{1}".format(self.__class__.__name__,
                                                     final_state))
        self.state = final_state

        super(StateMixin, self).__init__()
