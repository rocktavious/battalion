import os
import sys
import re
import logging
import six
import yaml
import traceback
from inspect import getdoc, cleandoc, isclass, getargspec, getcallargs
from pyul.coreUtils import DotifyDict
from docopt import docopt, DocoptExit

from .exceptions import NoSuchCommand
from .registry import CLIRegistrationMixin, HandlerRegistrationMixin, registry
from .state import StateMixin, State
from .log import enable_logging

LOG = logging.getLogger(__name__)


def cleanup_key(k):
    if k in ['<command>', '<args>']:
        return k
    if k.startswith('--'):
        k = k[2:]
    if k.startswith('-'):
        k = k[1:]
    k = k.replace('-', '_')
    k = k.replace('<', '')
    k = k.replace('>', '')
    return k


def get_command_args(command):
    args = [a for a in getargspec(command).args if a not in registry._fixtures.keys() and a != 'cli']
    return args


def get_command_spec(command, without_fixtures=True):
    spec = getargspec(command)
    positional = [None] * (len(spec.args) - len(spec.defaults or []))
    kwargs = getcallargs(command, *positional)
    kwargs.pop('cli')
    if without_fixtures:
        for name in registry._fixtures.keys():
            try:
                kwargs.pop(name)
            except KeyError:
                pass
    return kwargs

def format_command_args(command, kwargs):
    new_kwargs = {}
    command_kwargs = get_command_spec(command)
    for k, v in sorted(kwargs.items()):
        k = cleanup_key(k)
        # check if arg
        if v is None or v == 'None':
            v = new_kwargs.get(k, None) or command_kwargs.get(k, None) or None
        if k in command_kwargs:
            new_kwargs[k] = v
    return new_kwargs

def cleanup_data(data):
    new_data = {}
    for k, v in data.items():
        k = cleanup_key(k)
        new_data[k] = True if v == 'True' else v
    return DotifyDict(new_data)

def parse_argv(docstring, argv, docopt_kwargs={}):
    options = docopt(docstring,
                     argv,
                     **docopt_kwargs)
    return cleanup_data(options)


def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


class BaseCLI(StateMixin):
    """
    Base class for battalion commandline app
    """

    class State:
        cli = None
        version = 'UNKNOWN'
        options = [('-h, --help', 'Show this screen.'),
                   ('--version', 'Show version.')]

    def __init__(self, *args, **kwargs):
        super(BaseCLI, self).__init__(*args, **kwargs)
        self._name = self.__class__.__name__
        if not hasattr(self, '_key'):
            self._key = (self._name,)
        self._commands = registry.get_commands(self._key)
        self._handlers = registry.get_handlers(self._key) # [h for h in self._commands if isinstance(h, Handler)]
            

    def __getattr__(self, name):
        if name in self._commands:
            cmd = self._commands[name]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return CommandInvocation(cmd)
        raise AttributeError

    @property
    def docopt_options(self):
        return {'options_first': True,
                'version': self._state.version}

    def get_command(self, options):
        command_name, args = options.pop('<command>'), options.pop('<args>')
        if command_name is None or command_name is False:
            raise CommandExtractionError(self.docstring)
        try:
            command = self._commands[command_name]
        except KeyError:
            raise NoSuchCommand(command_name)
        return command, args

    def dispatch(self, argv):
        options = parse_argv(self.__autodoc__, argv, self.docopt_options)
        state.add_state(self._name, options)
        command, args = self.get_command(options)
        return self.run(command, args)

    def run(self, command, args):
        command_options = parse_argv(command.__autodoc__, args)
        kwargs = format_command_args(command, command_options)
        c = CommandInvocation(command)
        return c(**kwargs)


class AutoDocCommand(BaseCLI):
    """
    Class that supports generating the docopt docstrings for the class and
    it's command functions.
    """
    class State:
        default_config = None
        column_padding = 30

    def __init__(self, *args, **kwargs):
        super(AutoDocCommand, self).__init__(*args, **kwargs)
        # We check if autodoc has already happend so that
        # so that test frameworks can keep generating new
        # instances of the same class without redocumenting
        # which will cause a failure
        if self.__doc__ is None:
            self.__doc__ = ""
        if not hasattr(self, "__autodoc__"):
            self.generate_class_doc()
            self.generate_commands_doc()
            self.set_autodoc(self.docstring)

    @classmethod
    def set_autodoc(cls, docstring):
        cls.__autodoc__ = docstring

    @property
    def docstring(self):
        return cleandoc(self.__autodoc__)

    def generate_class_doc(self):
        LOG.debug('Documenting %s', self._name)
        new_doc = getdoc(self) or """{0}""".format(self._name)
        new_doc += "\n\n"
        new_doc += self.generate_usage()
        new_doc += self.generate_options()
        new_doc += self.generate_commands()
        self.__autodoc__ = cleandoc(new_doc)

    def generate_commands_doc(self):
        for name, func in self._commands.items():
            if isclass(func) and issubclass(func, Handler):
                LOG.debug('Documenting Command %s', name)
                self._commands[name] = func()
            else:
                LOG.debug('Documenting Command %s', name)
                new_command_doc = getdoc(func) or """{0}""".format(name)
                new_command_doc += "\n\n"
                new_command_doc += self.generate_command_usage(name, func)
                new_command_doc += self.generate_command_options(func)
                func.__autodoc__ = cleandoc(new_command_doc)
                self._commands[name] = func

    def generate_usage(self):
        docstring = ""
        if "Usage:" not in self.__doc__:
            docstring += "Usage:\n"
            docstring += "    {0} [options] <command> [<args>...]\n".format(self._name)
            docstring += "    {0} [options]\n\n".format(self._name)
        return docstring

    def generate_options(self):
        if "Options:" not in self.__doc__:
            docstring = "Options:\n"
            s = state[self._name]
            for flags, desc in s.options:
                if flags == '--config=<CONFIG>' and flags not in docstring:
                    if isinstance(self, CLI):
                        if s.default_config is None:
                            s.default_config = '~/.{name}/{name}.yaml'.format(name=self._name)
                        desc = desc.format(s.default_config)
                    else:
                        continue
                docstring += "    {0:<{2}} {1}\n".format(flags,
                                                         desc,
                                                         s.column_padding)
            docstring += "\n"
        return docstring

    def generate_commands(self):
        if "Commands:" not in self.__doc__:
            s = state[self._name]
            docstring = "Commands:\n"
            for k, v in self._commands.items():
                docstring += "    {0:<{2}} {1}\n".format(k,
                                                         getdoc(v),
                                                         s.column_padding)
            docstring += "\n"
        return docstring

    def generate_command_usage(self, name, command):
        docstring = ""
        if command.__doc__ is None or "Usage:" not in command.__doc__:
            docstring += "Usage:\n    {0} [options]\n".format(name)
            args = get_command_args(command)
            spec = get_command_spec(command)
            if args:
                docstring += "    {0} ".format(name)
                for arg_name in args:
                    if spec[arg_name] is not None:
                        docstring += "[<{0}>] ".format(arg_name)
                    else:
                        docstring += "<{0}> ".format(arg_name)
                docstring += "\n"
            docstring += "\n"
        return docstring

    def generate_command_options(self, command):
        docstring = ""
        if command.__doc__ is None or "Options:" not in command.__doc__:
            s = state[self._name]
            args = get_command_spec(command)
            if args:
                docstring += "Options:\n"
                for arg, default in args.items():
                    flag_def = "--{0}=<{1}>".format(arg,
                                                    arg.upper())
                    docstring += "    {0:<{3}} {1} [default: {2}]\n".format(flag_def,
                                                                            ' ',
                                                                            default,
                                                                            s.column_padding)
                docstring += "\n"
        return docstring


class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        for k, v in attrs.items():
            if registry.is_cached(v):
                registry.register(v, k, (clsname,))
        return newclass


@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDocCommand):
    class State:
        debug = False
        config = None
        dryrun = None
        options = [('-d, --debug', 'Show debug messages'),
                   ('--config=<CONFIG>', 'The config filepath [default: {0}]'),
                   ('--dryrun', 'If given any modifying actions will not be performed')]
        cwd = os.getcwd()

    @classmethod
    def main(cls, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        rv = cls()(*argv)
        if rv:
            print rv
        return rv

    def __init__(self):
        State(self)
        super(CLI, self).__init__()



    def __getattribute__(self, name):
        command = object.__getattribute__(self, name)
        commands = registry.get_commands((object.__getattribute__(self, '__class__').__name__,))
        if name in commands.keys():
            cmd = commands[name]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return CommandInvocation(cmd)
        return command

    def setup_logging(self):
        enable_logging(self._name, level=logging.INFO)

    def dispatch(self, argv):
        options = parse_argv(self.docstring, argv, self.docopt_options)
        options = cleanup_data(options)
        self.load_config(options)
        state.add_state(self._name, options)
        command, args = self.get_command(options)
        if isinstance(command, Handler):
            return command.dispatch(args)
        else:
            args.insert(0, command.func_name)
            return super(CLI, self).dispatch(argv)

    def load_config(self, options):
        config_filepath = os.path.abspath(os.path.expanduser(options.config))
        state[self._name].config = config_filepath
        if os.path.exists(config_filepath):
            with open(config_filepath, 'r') as ymlfile:
                config = DotifyDict(data=yaml.load(ymlfile))
                state.add_config(cleanup_data(config))
