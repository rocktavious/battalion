from __future__ import absolute_import
import os
import sys
import re
import logging
import six
import yaml
import traceback
from inspect import getdoc
from pyul.coreUtils import DotifyDict
from docopt import docopt, DocoptExit

from .exceptions import NoSuchCommand
from .registry import CLIRegistrationMixin, HandlerRegistrationMixin, registry
from .handler import HandlerMarker
from .autodoc import AutoDocCommand
from .state import state
from .log import enable_logging
from .utils import cleanup_data, CommandInvocation


LOG = logging.getLogger(__name__)


@six.add_metaclass(HandlerRegistrationMixin)
class Handler(AutoDocCommand, HandlerMarker):

    def __init__(self):
        super(Handler, self).__init__()

    def __call__(self, *args, **kwargs):
        print self.__autodoc__

    def __getattr__(self, attr):
        if attr in self.commands:
            cmd = self.commands[attr]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return CommandInvocation(cmd)
        raise AttributeError("Unable to find attr or command for {0}".format(attr))


@six.add_metaclass(CLIRegistrationMixin)
class CLI(AutoDocCommand):
    class State:
        options = [
            ('-d, --debug', 'Show debug messages'),
            ('--dryrun', 'If enabled any modifying actions will not be performed [default: False]')
        ]
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
        self.log = logging.getLogger(self.name)
        state.cli = self
        super(CLI, self).__init__()

    def __call__(self, *args):
        rv = None
        state.reinit()
        self.setup_logging()
        try:
            rv = self.dispatch(argv=" ".join(args))
        except KeyboardInterrupt:
            print "\nAborting."
            sys.exit(1)
        except NoSuchCommand as e:
            print "No such command: {0}".format(e.command)
            print "\n".join(parse_doc_section("commands:", getdoc(e.supercommand)))
            sys.exit(1)
        except DocoptExit as e:
            print e.message
            sys.exit(1)
        except SystemExit as e:
            sys.exit(e.code)
        except:
            traceback.print_exc()
            if hasattr(e, 'code'):
                sys.exit(e.code)
            else:
                sys.exit(1)
        finally:
            return rv

    def __getattr__(self, attr):
        if attr in self.commands:
            cmd = self.commands[attr]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return CommandInvocation(cmd)
        raise AttributeError("Unable to find attr or command for {0}".format(attr))

    @property
    def key(self):
        return (self.name,)

    def setup_logging(self):
        enable_logging(self.name, level=logging.INFO)

    def dispatch(self, argv):
        options = self.get_options(argv)
        self.load_config(options)
        command, args = self.get_command(options)
        if isinstance(command, Handler):
            return command.dispatch(args)
        else:
            args.insert(0, command.func_name)
            return super(CLI, self).dispatch(argv)

    def load_config(self, options):
        config_filepath = os.path.expanduser(options['--config'])
        self._state.config_file = config_filepath
        if os.path.exists(config_filepath):
            with open(self._state.config_file, 'r') as ymlfile:
                config = DotifyDict(data=yaml.load(ymlfile))
                state.add_config(cleanup_data(config))

def dryrun(f, value=None):
    def wrapper(*args, **kwargs):
        if state.dryrun is True:
            if isinstance(f, CommandInvocation):
                name = f.command.__name__
            else:
                name = f.__name__
            args = ','.join(list(args) + ["%s=%s" % (k, v) for (k, v) in kwargs.iteritems()])
            dryrun_logger = logging.getLogger(state.cli.name + '.dryrun')
            dryrun_logger.debug("DRYRUN: {0}({1})".format(name, args))
            return value
        else:
            return f(*args, **kwargs)
    return wrapper
