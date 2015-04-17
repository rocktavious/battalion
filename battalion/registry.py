import logging
import types
from inspect import isclass

LOG = logging.getLogger(__name__)


def copy_func(f, name=None):
    return types.FunctionType(f.func_code, f.func_globals, name or f.func_name,
        f.func_defaults, f.func_closure)


class Registry(object):

    def __init__(self):
        self._registry = {}
        self._cache = []
        self._aliases = {}
        self._fixtures = {}

    def get_commands(self, key):
        try:
            commands = self._registry[key]
        except KeyError:
            commands = {}
        return commands

    def is_cached(self, func):
        return func in self._cache

    def _register(self, key, func, name):
        LOG.debug('registering "%s" to "%s"', name, key)
        commands = self.get_commands(key)
        if name in commands.keys():
            raise ValueError("{0} already registered to {1}".format(name, key))
        if isclass(func):
            commands[name] = func
        else:
            # we copy the function so alias will show the proper usage line with the alias name
            commands[name] = copy_func(func, name)
        self._registry[key] = commands

    def register(self, func, name, key=None, aliases=[]):
        if func not in self._cache:
            LOG.debug('caching command "%s"', name)
            self._cache.append(func)
        if any(key):
            self._register(key, func, name)
            for alias in aliases:
                self._register(key, func, alias)
            for alias in [a for a, f in self._aliases.items() if f is func]:
                self._register(key, func, alias)
        else:
            for alias in aliases:
                LOG.debug('caching alias "%s" for command "%s"', alias, name)
                self._aliases[alias] = func

    def bind(self, func, cli, handler=None, aliases=[]):
        if handler:
            key = (cli, handler)
        else:
            key = (cli,)
        self.register(func, func.__name__, key, aliases)

    def get_fixture(self, key, state):
        try:
            fixture = self._fixtures[key]
        except KeyError:
            return None
        return fixture(state)

    def is_fixture(self, key):
        return key in self._fixtures.keys()

    def register_fixture(self, func, name):
        LOG.debug('registering fixture "%s"', name)
        if name in self._fixtures.keys():
            raise ValueError("{0} already a registered fixture".format(name))
        self._fixtures[name] = func


registry = Registry()


class HandlerRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None and newclass.State.cli != "self":
            registry.register(newclass, clsname, (newclass.State.cli,))
            for k, v in attrs.items():
                if registry.is_cached(v):
                    registry.register(v, k, (newclass.State.cli, clsname))
        return newclass


class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        for k, v in attrs.items():
            if registry.is_cached(v):
                registry.register(v, k, (clsname,))
        return newclass


def command(*args, **kwargs):
    """
    Decorator that can expose a function as a command for a cli or handler
    """
    invoked = bool(not args or kwargs)
    if not invoked:
        func, args = args[0], ()

    def register(func):
        name = func.__name__
        cli = kwargs.get('cli', None)
        handler = kwargs.get('handler', None)
        if handler:
            key = (cli, handler)
        else:
            key = (cli,)
        aliases = kwargs.get('aliases', [])
        if not isinstance(aliases, list):
            raise ValueError('command decorator aliases takes a list, ' \
                             'just use "alias" for a single string alias!')
        alias = kwargs.get('alias', [])
        if isinstance(alias, list):
            aliases += alias
        else:
            aliases += [alias]
        registry.register(func, name, key, aliases)
        return func
    return register if invoked else register(func)


def fixture(func, *args, **kwargs):
    """
    Decorator for a function that will be called ahead of the execution
    of a command that provides a return value to fill the commands
    argument with
    """
    registry.register_fixture(func, func.__name__)
    return func
