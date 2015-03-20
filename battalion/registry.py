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
        self._cache = {}

    def get_commands(self, key):
        try:
            commands = self._registry[key]
        except KeyError:
            commands = {}
        return commands

    def is_cached(self, name):
        return name in self._cache.keys()

    def _register(self, key, func, name):
        LOG.debug("registering", name, "to", key)
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
        if name not in self._cache.keys():
            LOG.debug("caching", name)
            self._cache[name] = (func, aliases)
        if any(key):
            self._register(key, func, name)
            for alias in aliases:
                self._register(key, func, alias)

    def bind(self, func, cli, handler=None, aliases=[]):
        if handler:
            key = (cli, handler)
        else:
            key = (cli,)
        self.register(func, func.__name__, key, aliases)


registry = Registry()


class HandlerRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None and newclass.State.cli != "self":
            registry.register(newclass, clsname, (newclass.State.cli,))
            for k, v in attrs.items():
                if registry.is_cached(k) and registry._cache[k][0] == v:
                    registry.register(v, k, (newclass.State.cli, clsname))
        return newclass


class CLIRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        for k, v in attrs.items():
            if registry.is_cached(k) and registry._cache[k][0] == v:
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
        alias = kwargs.get('alias', [])
        if isinstance(alias, list):
            aliases += alias
        else:
            aliases += [alias]
        registry.register(func, name, key, aliases)
        return func
    return register if invoked else register(func)
