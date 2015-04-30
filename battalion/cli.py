import sys
import traceback
from .registry import registry
from .autodoc import AutoDoc

class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        for k, v in attrs.items():
            if registry.is_cached(v):
                registry.register(v, k, (clsname,))
        return newclass


@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDoc):
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
        super(CLI, self).__init__()

    def __call__(self, *args):
        rv = None
        self.setup_logging()
        try:
            rv = self.dispatch(args=" ".join(args))
        except:
            traceback.print_exc()
            sys.exit(1)
        finally:
            return rv

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