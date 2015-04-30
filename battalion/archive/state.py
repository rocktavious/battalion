import logging
from copy import deepcopy
from pyul.coreUtils import DotifyDict


log = logging.getLogger(__name__)


class State(DotifyDict):
    """
    A class to provide a way to combine
     - state settings | by the programmer on a per class basis
     - config settings | by the users environment from a configuration file
    To produce a final "state" of the configuration at runtime
    """
    _instances = {}

    def __init__(self, cli):
        self.cli = cli
        self.cli_name = cli.__class__.__name__
        self.cli.log = logging.getLogger(self.cli_name)
        self.cli.state = self

    def _apply_state(self, namespace, data):
        if namespace not in self:
            self[namespace] = DotifyDict()
        for k, v in data.items():
            self[namespace][k] = v if v else self[namespace].get(k, v)

    def add_state(self, namespace, state):
        log.debug('Adding state {0}'.format(namespace))
        if namespace == self.cli_name:
            for k, v in state.items():
                self[k] = v if v is not None else self.get(k, v)
        self._apply_state(namespace, state)

    def add_config(self, config):
        for k, v in config.items():
            if k in self.cli.handlers:
                self._apply_state(k, v)
            elif k is self.cli.name:
                self._apply_state(self.cli.name, v)
            else:
                self[k] = v if v else self.get(k, v)


class StateMixin(object):
    """
    Mixin that provides static configuration settings to instance
    objects. State settings cannot start with a _.
    """

    def __init__(self, *args, **kwargs):
        # Get a List of all the Classes we in our MRO, find any attribute named
        #     State on them, and then merge them together in order of MRO
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

        self._state = final_state

        super(StateMixin, self).__init__()
