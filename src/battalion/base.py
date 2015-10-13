from __future__ import absolute_import
from docopt import docopt, DocoptExit
from inspect import cleandoc
from .exceptions import NoSuchCommand
from .registry import registry
from .handler import HandlerMarker
from .state import StateMixin, state
from .utils import cleanup_data, get_command_spec, CommandInvocation

class BaseCommand(StateMixin):
    """
    Base class for battalion commandline app
    """

    class State:
        cli = None
        version = 'UNKNOWN'
        default_config = None
        config_file = None
        options = [('-h, --help', 'Show this screen.'),
                   ('--version', 'Show version.')]

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def cli(self):
        return self._state.cli

    @property
    def key(self):
        return (self.cli, self.name)

    @property
    def commands(self):
        return registry.get_commands(self.key)

    @property
    def handlers(self):
        return [h for h in self.commands if isinstance(h, HandlerMarker)]

    @property
    def docstring(self):
        raise NotImplementedError

    @property
    def docopt_options(self):
        return {'options_first': True,
                'version': self._state.version}

    def format_command_args(self, command, kwargs):
        new_kwargs = {}
        command_kwargs = get_command_spec(command)
        for k, v in sorted(kwargs.items()):
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            k = k.replace('-', '_')
            k = k.replace('<', '')
            k = k.replace('>', '')
            # check if arg
            if v is None or v == 'None':
                v = new_kwargs.get(k, None) or command_kwargs.get(k, None) or None
            if k in command_kwargs:
                new_kwargs[k] = v
        return new_kwargs

    def get_options(self, argv):
        options = docopt(self.docstring,
                         argv,
                         **self.docopt_options)
        return options

    def get_command(self, options):
        command_name, args = options.pop('<command>'), options.pop('<args>')
        if command_name is None or command_name is False:
            raise SystemExit(self.docstring)
        try:
            command = self.commands[command_name]
        except KeyError:
            raise NoSuchCommand(command_name, self)
        state.add_state(cleanup_data(self._state))
        state.add_options(cleanup_data(options))
        return command, args

    def dispatch(self, argv):
        options = self.get_options(argv)
        command, args = self.get_command(options)
        return self.run(command, args)

    def run(self, command, args):
        command_options = docopt(cleandoc(command.__autodoc__), args)
        kwargs = self.format_command_args(command, command_options)
        state.compile()
        c = CommandInvocation(command)
        return c(**kwargs)