from inspect import getmro, isclass, isfunction

__registry__ = {}
__handlers__ = {}
__commands__ = {}

def command(func):
    __registry__[func.__name__] = func
    return func

def get_commands(name):
    return __commands__.get(name, {})

def get_handler(cli_name, handler_name):
    return __handlers__[cli_name][handler_name]

class CommandRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CommandRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None:
            try:
                cli_commands = __commands__[newclass.State.cli]
            except KeyError:
                cli_commands = {}
            cli_commands[clsname] = newclass
            __commands__[newclass.State.cli] = cli_commands
        for k, v in attrs.items():
            if isfunction(v):
                if k in __registry__.keys():
                    try:
                        cli_commands = __commands__[clsname]
                    except KeyError:
                        cli_commands = {}
                    cli_commands[k] = v
                    __commands__[clsname] = cli_commands
        return newclass


class HandlerRegistrationMixin(CommandRegistrationMixin):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(HandlerRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if hasattr(newclass.State, 'cli') and newclass.State.cli is not None:
            try:
                cli_handlers = __handlers__[newclass.State.cli]
            except KeyError:
                cli_handlers = {}
            cli_handlers[clsname] = newclass
            __handlers__[newclass.State.cli] = cli_handlers
        return newclass
