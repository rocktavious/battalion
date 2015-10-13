from __future__ import absolute_import
from inspect import getargspec, getcallargs
from pyul.coreUtils import DotifyDict
from .state import state
from .registry import registry


def cleanup_data(data):
    new_data = {}
    for k, v in data.items():
        if k.startswith('--'):
            k = k[2:]
        if k.startswith('-'):
            k = k[1:]
        k = k.replace('-', '_')
        if k in ['help', 'version', 'cli', 'options', 'column_padding', 'default_config', 'config']:
            continue
        new_data[k] = v
    return DotifyDict(new_data)


def get_command_args(command):
    args = [a for a in getargspec(command).args if a not in registry._fixtures.keys() and a != 'cli']
    return args


def get_command_spec(command, without_fixtures=True):
    spec = getargspec(command)
    positional = [None] * (len(spec.args) - len(spec.defaults or []))
    kwargs = getcallargs(command, *positional)
    if without_fixtures:
        for name in registry._fixtures.keys():
            try:
                kwargs.pop(name)
            except KeyError:
                pass
    return kwargs


def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


class CommandInvocation(object):

    def __init__(self, cmd):
        self.command = cmd

    def __call__(self, *args, **kwargs):
        command_kwargs = get_command_spec(self.command, without_fixtures=False)
        for k, v in sorted(command_kwargs.items()):
            if registry.is_fixture(k):
                kwargs[k] = registry.get_fixture(k, state)
        if state.debug:
            LOG.debug("State:\n{0}".format(state))
        return self.command(*args, **kwargs)