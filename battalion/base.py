import os
import sys
import traceback
import logging
import yaml
from pyul.coreUtils import synthesize, DotifyDict
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

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        synthesize(self, 'name', self.state.name or self.__class__.__name__)
        synthesize(self, 'config', {})

    def __call__(self, *args):
        rv = None
        self.argv = " ".join(args)
        try:
            rv = self.mainloop()
        except:
            traceback.print_exc()
            sys.exit(1)
        finally:
            return rv

    @property
    def docstring(self):
        return self.__doc__

    @property
    def docopt_options(self):
        return {'options_first': True,
                'version': self.state.version}

    def mainloop(self):
        self.setup_logging()
        self.parse_argv()
        self.load_config()
        self.configure()
        self.resolve()
        return self.dispatch()

    def setup_logging(self):
        enable_logging(self.name, level=logging.INFO)

    def configure(self):
        for k, v in self.config.items():
            if self.key == tuple(k.split('.')):
                self.state.update(v)

    def parse_argv(self):
        self.options = parse_args(self.docstring,
                                        self.argv,
                                        self.docopt_options)
        self.command = self.options.pop("<command>")
        self.args = self.options.pop("<args>")
        if self.command is None or self.command is False:
            raise CommandExtractionError(self.argv)

    def load_config(self):
        if self.options.config is not None:
            config_filepath = os.path.abspath(os.path.expanduser(self.options.config))
            if os.path.exists(config_filepath):
                with open(config_filepath, 'r') as ymlfile:
                    self.config = yaml.load(ymlfile)

    def resolve(self):
        key = self.key + (self.command,)
        if registry.is_handler(key):
            self.command = registry.get_handler(key)
        elif registry.is_command(key):
            self.command = registry.get_command(key)
        else:
            raise ValueError("Unable to find a command for: {0}".format(".".join(key)))

    def dispatch(self):
        self.command(*self.args)
