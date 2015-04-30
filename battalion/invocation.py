import logging
from .utils import get_command_spec

LOG = logging.getLogger(__name__)

def dryrun(f, value=None):
    def wrapper(*args, **kwargs):
        f.dryrun_value = value
        return f(*args, **kwargs)
    return wrapper


class CommandInvocation(object):

    def __init__(self, cli, cmd):
        self.cli = cli
        self.command = cmd
        self.dryrun_value = None

    def __call__(self, *args, **kwargs):
        command_kwargs = get_command_spec(self.command, without_fixtures=False)
        if state.debug:
            LOG.debug("State:\n{0}".format(state))
        if cli.dryrun:
            args = ','.join(args + ["%s=%s" % (k, v) for (k, v) in kwargs.iteritems()])
            dryrun_logger = logging.getLogger(self.cli.name + '.dryrun')
            dryrun_logger.debug("DRYRUN: {0}({1})".format(name, args))
            return self.dryrun_value
        else:
            return self.command(state.cli, *args, **kwargs)

    @property
    def docstring(self):
        try:
            return self.command.__autodoc__
        except AttributeError:
            return cleandoc(self.command.__doc__)