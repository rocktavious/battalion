import logging
import types
from inspect import cleandoc
from .invocation import CommandInvocation


LOG = logging.getLogger(__name__)


class Registry(object):

    def __init__(self):
        self._clis = {}
        self._commands = {}
        self._handlers = {}
        self._cache = []
        self._aliases = {}
        self._fixtures = {}

    def get_commands(self, key):
        commands = [(" ".join(k[-1:]), v) for k, v in self._commands.items()
                    if key == k[:-1]]
        output = dict(commands)
        return output

    def get_handlers(self, key):
        handlers = [(" ".join(k[-1:]), v) for k, v in self._handlers.items()
                    if key == k[:-1]]
        output = dict(handlers)
        return output

    def get_all(self, key):
        commands = [(" ".join(k[-1:]), v) for k, v in self._commands.items()
                    if key == k[:-1]]
        handlers = [(" ".join(k[-1:]), v) for k, v in self._handlers.items()
                    if key == k[:-1]]
        output = dict(commands + handlers)
        return output

    def get(self, key, collection):
        try:
            obj = collection[key]
        except KeyError:
            obj = None
        return obj

    def set(self, obj, key, collection):
        collection[key] = obj

    def is_type(self, key, collection):
        return key in collection.keys()
    
    def register(self, obj, key, collection, nicename):
        LOG.debug('registering %s %s to "%s"', nicename, obj, key)
        if key in collection.keys():
            raise ValueError("{0} already a registered {1}".format(key,
                                                                   nicename))
        collection[key] = obj

    def get_fixture(self, key, state):
        fixture = self.get(key, self._fixtures)
        if fixture is not None:
            fixture = fixture(state)
        return fixture

    def is_fixture(self, key):
        return self.is_type(key, self._fixtures)

    def register_fixture(self, obj, key):
        self.register(obj, key, self._fixtures, "fixture")

    def set_fixture(self, obj, key):
        self.set(obj, key, self._fixtures)

    def get_cli(self, key):
        return self.get(key, self._clis)

    def is_cli(self, key):
        return self.is_type(key, self._clis)
        
    def register_cli(self, obj, key):
        self.register(obj, key, self._clis, "cli")

    def set_cli(self, obj, key):
        self.set(obj, key, self._clis)

    def get_handler(self, key):
        return self.get(key, self._handlers)

    def is_handler(self, key):
        return self.is_type(key, self._handlers)
        
    def register_handler(self, obj, key):
        self.register(obj, key, self._handlers, "handler")

    def set_handler(self, obj, key):
        self.set(obj, key, self._handlers)

    def get_command(self, key):
        return self.get(key, self._commands)

    def is_cached(self, obj):
        return obj in self._cache
    
    def is_command(self, key):
        return self.is_type(key, self._commands)
        
    def register_command(self, obj, key=None, aliases=[]):
        if key is None:
            if obj not in self._cache:
                LOG.debug('caching %s', obj)
                self._cache.append(obj)
            for alias in aliases:
                LOG.debug('caching alias "%s" for command %s', alias, obj)
                self._aliases[alias] = obj
        else:
            if isinstance(key, tuple) is not True:
                key = (key,)
            self.register(obj, key, self._commands, "command")
            for alias in aliases:
                new_key = key[:-1] + (alias,)
                self.register(obj, new_key, self._commands, "command")
            for alias in [a for a, f in self._aliases.items() if f is obj]:
                new_key = key[:-1] + (alias,)
                self.register(obj, new_key, self._commands, "command")

    def set_command(self, obj, key):
        self.set(obj, key, self._commands)

    def bind(self, func, cli, handler=None, aliases=[]):
        key = (cli,)
        if handler:
            key += (handler,)
        self.register_command(func, key, aliases)


registry = Registry()
