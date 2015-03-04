import sys
import re
import logging
import six
import types
from decorator import decorator
from inspect import getdoc, cleandoc, isfunction, ismethod, getargspec
from pyul.coreUtils import synthesize
from .exceptions import NoSuchCommand, CommandMissingDefaults
from .parse import docopt, parse_doc_section, DocoptExit
from .registry import HandlerRegistrationMixin, CommandRegistrationMixin, get_commands, get_handler
from .state import StateMixin

log = logging.getLogger(__name__)

def get_command_spec(command):
    spec = getargspec(command)
    args = [a for a in spec.args if a != "self"]
    defaults = spec.defaults
    if args:
        if len(args) != len(defaults):
            raise CommandMissingDefaults(command)
        args = dict(zip(args, defaults))
    return args
    

@six.add_metaclass(CommandRegistrationMixin)
class BaseCommand(StateMixin):
    """
    Base class for battalion commandline app
    """

    class State:
        version = 'UNKNOWN'
        options = [('-h --help', 'Show this screen.'),
                   ('-d --debug', 'Show debug messages.'),
                   ('--version', 'Show version.')]

    def __init__(self):
        super(BaseCommand, self).__init__()
        synthesize(self, 'name', self.__class__.__name__)
        synthesize(self, 'commands', get_commands(self.name), readonly=True)

    def format_handler_args(self, handler, kwargs):
        new_kwargs = {}
        handler_kwargs = get_command_spec(handler)
        for k, v in kwargs.items():
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            new_kwargs[k] = v or handler_kwargs[k]
        return new_kwargs

    def docopt_options(self):
        return {'options_first': True,
                'version': self._state.version}
    
    def get_command(self, argv):
        docstring = getdoc(self)
        options = docopt(docstring,
                         argv,
                         **self.docopt_options())
        return options['COMMAND'], options.get('COMMAND_ARGS', [])
    
    def get_handler(self, command, command_args):
        if command is None:
            raise SystemExit(self.__doc__)
        try:
            handler = getattr(self, command)
        except AttributeError:
            raise NoSuchCommand(command, self)
        handler_docstring = getdoc(handler)

        if handler_docstring is None:
            raise NoSuchCommand(command, self)

        handler_args = docopt(handler_docstring,
                              command_args,
                              **self.docopt_options())

        return handler, handler_args

    def dispatch(self, argv):
        self.run(*self.get_handler(*self.get_command(argv)))

    def run(self, handler, handler_args):
        if ismethod(handler):
            handler(**self.format_handler_args(handler,
                                               handler_args))
        else:
            handler().dispatch(handler_args)


class AutoDocCommand(BaseCommand):
    """
    Class that supports generating the docopt docstrings for the class and
    it's command functions.
    """
    class State:
        column_padding = 20
    
    def __init__(self):
        super(AutoDocCommand, self).__init__()
        new_doc = getdoc(self) or """{0}""".format(self.name)
        new_doc += "\n\n"
        new_doc += self.generate_usage()
        new_doc += self.generate_options()
        new_doc += self.generate_commands()
        self.__doc__ = cleandoc(new_doc)
        
        for command_name, command_function in self.commands.items():
            if isfunction(command_function):
                new_command_doc = getdoc(command_function) or """{0}""".format(command_name)
                new_command_doc += "\n\n"
                new_command_doc += self.generate_command_usage(command_name, command_function)
                if "Options:" not in new_command_doc:
                    new_command_doc += self.generate_command_options(command_name, command_function)
                command_function.__doc__ = cleandoc(new_command_doc)

    def generate_usage(self):
        docstring = "Usage:\n    {0} [options] [COMMAND]\n\n".format(self.name)
        return docstring

    def generate_options(self):
        docstring = ""
        if self._state.options:
            docstring += "Options:\n"           
            for flags, desc in self._state.options:
                docstring += "    {0:<{2}} {1}\n".format(flags,
                                                         desc,
                                                         self._state.column_padding)
            docstring += "\n"

        return docstring

    def generate_commands(self):
        docstring = ""
        if self.commands:
            docstring += "Commands:\n"
            for k, v in self.commands.items():
                docstring += "    {0:<{2}} {1}\n".format(k,
                                                             getdoc(v),
                                                             self._state.column_padding)
            docstring += "\n"

        return docstring
    
    def generate_command_usage(self, command_name, command_function):
        docstring = "Usage:\n    {0}".format(command_name)
        if get_command_spec(command_function):
            docstring += " [options]"
        
        docstring += "\n\n"
        return docstring
    
    def generate_command_options(self, command_name, command_function):
        docstring = ""
        args = get_command_spec(command_function)
        if args:
            docstring += "Options:\n"           
            for arg, default in args.items():
                docstring += "    --{0} <{1}> docstring description [default: {2}]\n".format(arg,
                                                                       arg.upper(),
                                                                       default)
            docstring += "\n"
        
        return docstring


@six.add_metaclass(HandlerRegistrationMixin)
class Handler(AutoDocCommand):
    
    class State:
        cli = None

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

    def setup_logging(self):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter())
        console_handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)

    def get_handler(self, command, command_args):
        try:
            handler = get_handler(self.name, command)
        except KeyError:
            handler, command_args = super(CLI, self).get_handler(command, command_args)

        return handler, command_args

    @classmethod
    def main(cls):
        cls()()


