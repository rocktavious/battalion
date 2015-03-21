import os
import sys
import re
import logging
import six
import yaml
from functools import partial
from inspect import getdoc, cleandoc, isclass, getargspec
from pyul.coreUtils import DotifyDict, synthesize
from docopt import docopt

from .exceptions import NoSuchCommand, CommandMissingDefaults
from .registry import CLIRegistrationMixin, HandlerRegistrationMixin, registry
from .state import StateMixin, state

LOG = logging.getLogger(__name__)

def cleanup_data(data):
    new_data = {}
    for k, v in data.items():
        if k.startswith('--'):
            k = k[2:]
        if k.startswith('-'):
            k = k[1:]
        k = k.replace('-', '_')
        if k in ['help', 'version', 'cli', 'options', 'column_padding', 'default_config', 'config']:
            continue
        new_data[k] = v
    return DotifyDict(new_data)

def get_command_spec(command):
    spec = getargspec(command)
    args = [a for a in spec.args if a != "cli"]
    defaults = spec.defaults
    kwargs = {}
    if args and defaults:
        if len(args) != len(defaults):
            raise CommandMissingDefaults(command)
        kwargs = dict(zip(args, defaults))
    return kwargs


def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


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
    def handler(self):
        return None

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
        return [h for h in self.commands if isinstance(h, Handler)]

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
        for k, v in kwargs.items():
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            k = k.replace('-', '_')
            if v is None:
                v = command_kwargs[k] or None
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
        self.run(command, args)

    def run(self, command, args):
        command_options = docopt(cleandoc(command.__autodoc__), args)
        kwargs = self.format_command_args(command, command_options)
        state.add_options(kwargs)
        state.compile()
        
        if state.debug:
            print "State:", state
        command(state.cli, **kwargs)


class AutoDocCommand(BaseCommand):
    """
    Class that supports generating the docopt docstrings for the class and
    it's command functions.
    """
    class State:
        column_padding = 30

    def __init__(self):
        super(AutoDocCommand, self).__init__()
        self.generate_class_doc()
        self.generate_commands_doc()

    @property
    def docstring(self):
        return cleandoc(self.__autodoc__)

    def generate_class_doc(self):
        LOG.debug('Documenting', self.name)
        new_doc = getdoc(self) or """{0}""".format(self.name)
        new_doc += "\n\n"
        new_doc += self.generate_usage()
        new_doc += self.generate_options()
        new_doc += self.generate_commands()
        self.__autodoc__ = cleandoc(new_doc)

    def generate_commands_doc(self):
        for name, func in self.commands.items():
            if isclass(func) and issubclass(func, Handler):
                LOG.debug('Documenting Command', name)
                self.commands[name] = func()
            else:
                LOG.debug('Documenting Command', name)
                new_command_doc = getdoc(func) or """{0}""".format(name)
                new_command_doc += "\n\n"
                new_command_doc += self.generate_command_usage(name, func)
                new_command_doc += self.generate_command_options(func)
                func.__autodoc__ = cleandoc(new_command_doc)
                self.commands[name] = func

    def generate_usage(self):
        docstring = ""
        if "Usage:" not in self.__doc__:
            docstring += "Usage:\n"
            docstring += "    {0} [options] <command> [<args>...]\n".format(self.name)
            docstring += "    {0} [options]\n\n".format(self.name)
        return docstring

    def generate_options(self):
        if "Options:" not in self.__doc__:
            docstring = "Options:\n"
            for flags, desc in self._state.options:
                if flags == '--config=<CONFIG>' and flags not in docstring:
                    if isinstance(self, CLI):
                        if self._state.default_config is None:
                            self._state.default_config = '~/.{name}/{name}.yaml'.format(name=self.name)
                        desc = desc.format(self._state.default_config)
                    else:
                        continue
                docstring += "    {0:<{2}} {1}\n".format(flags,
                                                         desc,
                                                         self._state.column_padding)
            docstring += "\n"
        return docstring

    def generate_commands(self):
        if "Commands:" not in self.__doc__:
            docstring = "Commands:\n"
            for k, v in self.commands.items():
                docstring += "    {0:<{2}} {1}\n".format(k,
                                                         getdoc(v),
                                                         self._state.column_padding)
            docstring += "\n"
        return docstring

    def generate_command_usage(self, name, command):
        docstring = ""
        if "Usage:" not in command.__doc__:
            docstring += "Usage:\n    {0} [options]\n\n".format(name)
        return docstring

    def generate_command_options(self, command):
        docstring = ""
        if "Options:" not in command.__doc__:
            args = get_command_spec(command)
            if args:
                docstring += "Options:\n"
                for arg, default in args.items():
                    flag_def = "--{0}=<{1}>".format(arg,
                                                    arg.upper())
                    docstring += "    {0:<{3}} {1} [default: {2}]\n".format(flag_def,
                                                                            ' ',
                                                                            default,
                                                                            self._state.column_padding)
                docstring += "\n"
        return docstring


@six.add_metaclass(HandlerRegistrationMixin)
class Handler(AutoDocCommand):

    def __init__(self):
        super(Handler, self).__init__()
        
    def __getattr__(self, name):
        if name in self.commands:
            return partial(self.commands[name], state.cli)
        raise AttributeError


@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDocCommand):
    class State:
        options = [('-d, --debug', 'Show debug messages'),
                   ('--config=<CONFIG>', 'The config filepath [default: {0}]')]

    @classmethod
    def main(cls):
        cls()()
        
    def __init__(self):
        state.cli = self
        super(CLI, self).__init__()

    def __call__(self):
        try:
            self.setup_logging()
            self.dispatch(argv=sys.argv[1:])
        except KeyboardInterrupt:
            LOG.error("\nAborting.")
            sys.exit(1)
        except NoSuchCommand as e:
            LOG.error("No such command: %s", e.command)
            LOG.error("")
            LOG.error("\n".join(parse_doc_section("commands:", getdoc(e.supercommand))))
            sys.exit(1)
            
    def __getattr__(self, name):
        if name in self.commands:
            cmd = self.commands[name]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return partial(cmd, self)
        raise AttributeError

    @property
    def key(self):
        return (self.name,)

    def setup_logging(self):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter())
        console_handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

    def dispatch(self, argv):
        options = self.get_options(argv)
        self.load_config(options)
        command, args = self.get_command(options)
        if isinstance(command, Handler):
            command.dispatch(args)
        else:
            args.insert(0, command.func_name)
            super(CLI, self).dispatch(argv)

    def load_config(self, options):
        config_filepath = os.path.expanduser(options['--config'])
        self._state.config_file = config_filepath
        if os.path.exists(config_filepath):
            with open(self._state.config_file, 'r') as ymlfile:
                config = DotifyDict(data=yaml.load(ymlfile))
                state.add_config(cleanup_data(config))
