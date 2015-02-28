import sys
import re
import logging
import six
from inspect import getdoc
from docopt import docopt, DocoptExit

log = logging.getLogger(__name__)

__handlers__ = {}

def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]    

class NoSuchCommand(ValueError):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)

        self.command = command
        self.supercommand = supercommand

class HandlerRegistrationMixin(type):
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
    
class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname != 'CLI':
            __handlers__[clsname] = {}
        return newclass
    
class Command(object):
    version = ''

    def docopt_options(self):
        return {'options_first': True,
                'version': self.version}
    
    def fixup_args(self, args):
        output = {}
        for k, v in args.items():
            output[k.replace('--', '')] = v
        
        return output
    
    def get_command(self, argv):
        return argv, argv[0], argv[1:]
    
    def get_handler(self, command, command_args):
        handler = getattr(self, command)
        handler_docstring = getdoc(handler)

        if handler_docstring is None:
            raise NoSuchCommand(command, self)

        handler_args = docopt(handler_docstring,
                              command_args,
                              **self.docopt_options())

        
        return handler, self.fixup_args(handler_args)

    def parse(self, argv):
        options, command, command_args = self.get_command(argv)
        handler, handler_args = self.get_handler(command, command_args)
        return options, handler, handler_args

    def dispatch(self, argv):
        self.run(*self.parse(argv))

    def run(self, options, handler, handler_args):
        handler(**handler_args)

@six.add_metaclass(HandlerRegistrationMixin)
class Handler(Command):
    cli = None

@six.add_metaclass(CLIRegistrationMixin)
class CLI(Command):
    
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
            raise NoSuchCommand(command, self)

        return handler, command_args

    def run(self, options, handler, handler_args):
        handler().dispatch(handler_args)

    @classmethod
    def main(cls):
        cls()()


