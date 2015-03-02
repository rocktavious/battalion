import sys
import re
import logging
import six
import types
from decorator import decorator
from inspect import getdoc, cleandoc, isfunction, ismethod, getargspec
from pyul.coreUtils import synthesize
from .parse import docopt, parse_doc_section, DocoptExit

log = logging.getLogger(__name__)


__registry__ = {}
__handlers__ = {}
__commands__ = {}

def command(func):
    __registry__[func.__name__] = func
    return func

class NoSuchCommand(ValueError):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)

        self.command = command
        self.supercommand = supercommand
    

class CommandRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CommandRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname not in ['CLI', 'Handler']:
            if issubclass(newclass, Handler):
                try:
                    cli_commands = __commands__[newclass.cli]
                except KeyError:
                    cli_commands = {}
                cli_commands[clsname] = newclass
                __commands__[newclass.cli] = cli_commands
            for k, v in attrs.items():
                if isfunction(v):
                    if k in __registry__.keys():
                        try:
                            cli_commands = __commands__[clsname]
                        except KeyError:
                            cli_commands = {}
                        cli_commands[k] = v
                        __commands__[clsname] = cli_commands
        return newclass


class HandlerRegistrationMixin(CommandRegistrationMixin):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname != 'Handler':
            if newclass.cli == None:
                raise ValueError('Please define which `CLI` handler {0} is for'.format(clsname))
            try:
                cli_handlers = __handlers__[newclass.cli]
            except KeyError:
                cli_handlers = {}
            cli_handlers[clsname] = newclass
            __handlers__[newclass.cli] = cli_handlers
        return newclass


class CLIRegistrationMixin(CommandRegistrationMixin):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname != 'CLI':
            __handlers__[clsname] = {}
        return newclass


class Base(object):
    version = ''
    doc_column_padding = 20
    options = [('-h --help', 'Show this screen.'),
               ('-d --debug', 'Show debug messages.'),
               ('--version', 'Show version.')]
    commands = {}
    
    def __init__(self):
        #auto doc
        synthesize(self, 'name', self.__class__.__name__)
        self.commands = __commands__.get(self.name)
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
                
    
    def fixup_kwargs(self, handler, kwargs):
        args = self.command_has_options(handler.__name__, handler)
        new_kwargs = {}
        for k, v in kwargs.items():
            if k.startswith('--'):
                k = k[2:]
            if k.startswith('-'):
                k = k[1:]
            new_kwargs[k] = v or args[k]
        return new_kwargs
    
    def generate_usage(self):
        docstring = "Usage:\n    {0} [options] [COMMAND]\n\n".format(self.name)
        return docstring

    def generate_options(self):
        docstring = ""
        if self.options:
            docstring += "Options:\n"           
            for flags, desc in self.options:
                docstring += "    {0:<{2}} {1}\n".format(flags,
                                                         desc,
                                                         self.doc_column_padding)
            docstring += "\n"

        return docstring

    def generate_commands(self):
        docstring = ""
        if self.commands:
            docstring += "Commands:\n"
            for k, v in self.commands.items():
                docstring += "    {0:<{2}} {1}\n".format(k,
                                                             getdoc(v),
                                                             self.doc_column_padding)
            docstring += "\n"

        return docstring
    
    def generate_command_usage(self, command_name, command_function):
        docstring = "Usage:\n    {0}".format(command_name)
        if self.command_has_options(command_name, command_function):
            docstring += " [options]"
        
        docstring += "\n\n"
        return docstring
    
    def command_has_options(self,command_name, command_function):
        spec = getargspec(command_function)
        args = [a for a in spec.args if a != "self"]
        if args:
            if len(args) != len(spec.defaults):
                raise ValueError("command '{0}' does not have defaults for every argument it takes\n  ARGS: {1}\n DEFAULTS: {2}".format(command_name,
                                                                                                                                      args,
                                                                                                                                      spec.defaults))
            args = dict(zip(args, spec.defaults))
        return args
        
    
    def generate_command_options(self, command_name, command_function):
        docstring = ""
        args = self.command_has_options(command_name, command_function)
        if args:
            docstring += "Options:\n"           
            for arg, default in args.items():
                docstring += "    --{0} <{1}> docstring description [default: {2}]\n".format(arg,
                                                                       arg.upper(),
                                                                       default)
            docstring += "\n"
        
        return docstring
        
        

    def docopt_options(self):
        return {'options_first': True,
                'version': self.version}
    
    def get_command(self, argv):
        docstring = getdoc(self)
        options = docopt(docstring,
                         argv,
                         **self.docopt_options())
        return options, options['COMMAND'], options.get('COMMAND_ARGS', [])
    
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

    def parse(self, argv):
        options, command, command_args = self.get_command(argv)
        handler, handler_args = self.get_handler(command, command_args)
        return options, handler, handler_args

    def dispatch(self, argv):
        self.run(*self.parse(argv))

    def run(self, options, handler, handler_args):
        handler(**self.fixup_kwargs(handler=handler, kwargs=handler_args))

@six.add_metaclass(HandlerRegistrationMixin)
class Handler(Base):
    cli = None

@six.add_metaclass(CLIRegistrationMixin)
class CLI(Base):
    
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
            handler = __handlers__[self.__class__.__name__][command]
        except KeyError:
            handler, command_args = super(CLI, self).get_handler(command, command_args)

        return handler, command_args

    def run(self, options, handler, handler_args):
        if ismethod(handler):
            handler(**self.fixup_kwargs(kwargs=handler_args))
        else:
            handler().dispatch(handler_args)

    @classmethod
    def main(cls):
        cls()()


