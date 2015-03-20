from inspect import getargspec


class NoSuchCommand(ValueError):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)
        self.command = command
        self.supercommand = supercommand


class CommandMissingDefaults(ValueError):
    def __init__(self, command):
        spec = getargspec(command)
        msg = """
        command '{0}' does not have defaults for every argument it takes
        ARGS: {1}
        DEFAULTS: {2}
        """
        super(CommandMissingDefaults, self).__init__(msg.format(command.__name__,
                                                                spec.args[1:],
                                                                spec.defaults))
