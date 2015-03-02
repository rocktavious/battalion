from inspect import getmro

__registry__ = {}
__handlers__ = {}
__commands__ = {}

def command(func):
    __commands__[func.__name__] = func
    return func

class CommandRegistrationMixin(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CommandRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname not in ['CLI', 'Handler']:
            if issubclass(newclass, Handler):
                try:
                    cli_commands = __commands__[newclass.cli]
                except KeyError:
                    cli_commands = {}
                cli_commands[clsname] = newclass
                __commands__[newclass.cli] = cli_commands
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
        if clsname != 'Handler':
            if newclass.cli == None:
                raise ValueError('Please define which `CLI` handler {0} is for'.format(clsname))
            try:
                cli_handlers = __handlers__[newclass.cli]
            except KeyError:
                cli_handlers = {}
            cli_handlers[clsname] = newclass
            __handlers__[newclass.cli] = cli_handlers
        return newclass


class CLIRegistrationMixin(CommandRegistrationMixin):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(CLIRegistrationMixin, cls).__new__(cls, clsname, bases, attrs)
        if clsname != 'CLI':
            __handlers__[clsname] = {}
        return newclass