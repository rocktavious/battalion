import six
from .registry import registry
from .autodoc import AutoDoc


class HandlerRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None and newclass.State.cli != "self":
            registry.register_handler(newclass, (newclass.State.cli, clsname))
            for k, v in attrs.items():
                if registry.is_cached(v):
                    registry.register_command(v, (newclass.State.cli, clsname, k))
        return newclass


@six.add_metaclass(HandlerRegistrationMixin)
class Handler(AutoDoc):
    _is_handler = True

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        registry.set_handler(self, self.key)

    @property
    def key(self):
        return (self.state.cli, self.name)