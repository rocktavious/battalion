import sys
import re
import logging
import six
from inspect import getdoc, cleandoc, isclass, getargspec
from pyul.coreUtils import DotifyDict
from docopt import docopt, DocoptExit
from functools import partial

from .exceptions import NoSuchCommand, CommandMissingDefaults
from .registry import CLIRegistrationMixin, HandlerRegistrationMixin, registry
from .state import StateMixin

LOG = logging.getLogger(__name__)

def get_command_spec(command):
    spec = getargspec(command)
    args = [a for a in spec.args if a != "options"]
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
        options = [('-h, --help', 'Show this screen.'),
                   ('--version', 'Show version.'),
                   ('-d, --debug=<DEBUG>', 'Show debug messages. [default: False]')]

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

    def format_command_args(self, handler, kwargs):
        new_kwargs = {}
        handler_kwargs = get_command_spec(handler)
        for k, v in kwargs.items():
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            if v is None:
                v = handler_kwargs[k] or None
            new_kwargs[k] = v
        return new_kwargs
    
    def format_options(self, kwargs):
        new_kwargs = {}
        for k, v in kwargs.items():
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            if k == 'debug':
                if v == 'True':
                    v = True
                else:
                    v = False
            new_kwargs[k] = v
        return DotifyDict(new_kwargs)

    def docopt_options(self):
        return {'options_first': True,
                'version': self._state.version}
    
    def get_command(self, argv):
        docstring = cleandoc(self.__autodoc__)
        options = docopt(docstring,
                         argv,
                         **self.docopt_options())
        name, args = options.pop('COMMAND'), options.pop('ARGS', [])
        if name is None:
            raise SystemExit(self.__autodoc__)
        try:
            command = self.commands[name]
        except KeyError:
            raise NoSuchCommand(name, self)
        
        if isinstance(command, Handler):
            command = partial(command.dispatch, args)
        else:
            command_options = docopt(cleandoc(command.__autodoc__),
                                     args)            
            kwargs = self.format_command_args(command, command_options)
            options = self.format_options(options)
            command = partial(command, options, **kwargs)
        
        return command

    def dispatch(self, argv):
        self.run(self.get_command(argv))

    def run(self, command):
        command()


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
            docstring += "Usage:\n    {0} [options] [COMMAND] [ARGS...]\n\n".format(self.name)
        return docstring

    def generate_options(self):
        if "Options:" not in self.__doc__:
            docstring = "Options:\n"           
            for flags, desc in self._state.options:
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
    pass

@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDocCommand):
    
    def __call__(self):
        try:
            self.setup_logging()
            self.dispatch(sys.argv[1:])
        except KeyboardInterrupt:
            log.error("\nAborting.")
            sys.exit(1)
        except NoSuchCommand as e:
            log.error("No such command: %s", e.command)
            log.error("")
            log.error("\n".join(parse_doc_section("commands:", getdoc(e.supercommand))))
            sys.exit(1)
    
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

    @classmethod
    def main(cls):
        cls()()


