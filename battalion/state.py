from pyul.coreUtils import DotifyDict, synthesize

class State(DotifyDict):
    """
    A class to provide a way to combine
     - state settings | by the programmer
     - config settings | by the users environment
     - options settings | by the user at command runtime
    To produce a final "state" of the configuration
    """

    def __init__(self):
        self.cli = None
        self.state_list = list()
        self.options_list = list()
        self.config_list = list()

    def add_options(self, options):
        self.options_list.append(options)
    
    def add_state(self, state):
        self.state_list.append(state)
    
    def add_config(self, config):
        self.config_list.append(config)
    
    def compile(self):
        for state in reversed(self.state_list):
            self.update(state)

        for config in self.config_list:
            self.update(config)

        for option in self.options_list:
            self.update(option)
        
        self.pop('state_list')
        self.pop('config_list')
        self.pop('options_list')
        self.cli.state = self
        for handler in self.cli.handlers:
            handler.state = self

state = State()

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
        for state in states:
            final_state.update(DotifyDict(dict([x for x in state.__dict__.items()
                                           if not x[0].startswith("_")])))

        # Update the final state with any kwargs passed in
        for key in final_state.keys():
            if key in kwargs:
                final_state[key] = kwargs.pop(key)

        self._state = final_state

        super(StateMixin, self).__init__()
