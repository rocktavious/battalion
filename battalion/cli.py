import os
import sys
import traceback
import six
import yaml
from pyul.coreUtils import synthesize, DotifyDict
from .registry import registry
from .autodoc import AutoDoc
from .utils import parse_args
from .exceptions import CommandExtractionError, NoSuchCommand

class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        registry.register_cli(newclass, (clsname,))
        for k, v in attrs.items():
            if registry.is_cached(v):
                registry.register_command(v, (clsname, k))
        return newclass


@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDoc):
    class State:
        debug = False
        options = [('-d, --debug', 'Show debug messages'),
                   ('--config=<CONFIG>', 'The config filepath [default: {0}]'),
                   ('--dryrun', 'If given any modifying actions wrapped in dryrun will not be performed')]
        cwd = os.getcwd()

    @property
    def key(self):
        return (self.name,)

    @classmethod
    def main(cls, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        rv = cls()(*argv)
        if rv:
            print rv
        return rv

    def __init__(self):
        super(CLI, self).__init__()
        registry.set_cli(self, self.key)

    #def __getattribute__(self, name):
        #command = object.__getattribute__(self, name)
        #commands = registry.get_commands((object.__getattribute__(self, '__class__').__name__,))
        #if name in commands.keys():
            #cmd = commands[name]
            #if isinstance(cmd, Handler):
                #return cmd
            #else:
                #return CommandInvocation(cmd)
        #return command
