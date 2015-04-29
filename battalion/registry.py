import logging
import types


LOG = logging.getLogger(__name__)


def copy_func(f, name=None):
    return types.FunctionType(f.func_code, f.func_globals, name or f.func_name,
        f.func_defaults, f.func_closure)


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
        return self.command(state.cli, *args, **kwargs)


class Registry(object):

    def __init__(self):
        self._commands = {}
        self._handlers = {}
        self._cache = []
        self._aliases = {}
        self._fixtures = {}

    def get_commands(self, key):
        try:
            commands = self._commands[key]
        except KeyError:
            commands = {}
            self._commands[key] = commands
        return commands

    def get_handlers(self, key):
        try:
            handlers = self._handlers[key]
        except KeyError:
            handlers = {}
            self._handlers[key] = handlers
        return handlers

    def is_cached(self, func):
        return func in self._cache

    def _register(self, key, func, name):
        LOG.debug('registering "%s" to "%s"', name, key)
        commands = self.get_commands(key)
        handlers = self.get_handlers(key)
        if name in commands.keys() or name in handlers.keys():
            raise ValueError("{0} already registered to {1}".format(name, key))
        if hasattr(func, '_is_handler'):
            handlers[name] = func
        else:
            # we copy the function so alias will show the proper usage line with the alias name
            commands[name] = CommandInvocation(types.FunctionType(func.func_code,
                                                                  func.func_globals,
                                                                  name))

    def register(self, func, name, key=None, aliases=[]):
        if func not in self._cache:
            LOG.debug('caching "%s"', name)
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
