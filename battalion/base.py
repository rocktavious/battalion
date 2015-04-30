import sys
from pyul.coreUtils import synthesize
from .log import enable_logging
from .state import StateMixin
from .registry import registry
from .utils import parse, parse_args, format_command_args
from .exceptions import NoSuchCommand, CommandExtractionError

class Base(StateMixin):
    """
    Base class for battalion commandline app
    """

    class State:
        name = None
        cli = None
        version = 'UNKNOWN'
        options = [('-h, --help', 'Show this screen.'),
                   ('--version', 'Show version.')]

    def __init__(self, key=None, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        synthesize(self, 'name', self._state.name or self.__class__.__name__)
        synthesize(self, 'key', key or (self.name,))
        synthesize(self, 'commands', registry.get_commands(self.key))
        synthesize(self, 'handler', registry.get_handlers(self.key))

    @property
    def docstring(self):
        return self.__doc__

    @property
    def docopt_options(self):
        return {'options_first': True,
                'version': self._state.version}

    def setup_logging(self):
        enable_logging(self.name, level=logging.INFO)

    def dispatch(self, args):
        options, command, command_args = parse(self.docstring,
                                               args,
                                               self.key,
                                               self.docopt_options)
        command_options = parse_args(command.docstring, command_args)
        kwargs = format_command_args(command, command_options)
        return command(**kwargs)
