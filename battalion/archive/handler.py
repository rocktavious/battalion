from .registry import registry


class HandlerRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None and newclass.State.cli != "self":
            registry.register(newclass, clsname, (newclass.State.cli,))
            for k, v in attrs.items():
                if registry.is_cached(v):
                    registry.register(v, k, (newclass.State.cli, clsname))
        return newclass


@six.add_metaclass(HandlerRegistrationMixin)
class Handler(AutoDocCommand):
    _is_handler = True

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self._key = (self.state.cli, self._name)

    def __call__(self, *args, **kwargs):
        print self.__autodoc__

    def __getattribute__(self, name):
        command = object.__getattribute__(self, name)
        commands = registry.get_commands((self.state.cli.name, object.__getattribute__(self, '__class__').__name__))
        if name in commands.keys():
            cmd = commands[name]
            if isinstance(cmd, Handler):
                return cmd
            else:
                return CommandInvocation(cmd)
        return command