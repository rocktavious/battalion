__all__ = ['NoSuchCommand']

class CommandExtractionError(ValueError):
    def __init__(self, options):
        msg = "Unable to extract command from: {0}".format(options)
        super(CommandExtractionError, self).__init__(msg)
        self.options = options

class NoSuchCommand(ValueError):
    def __init__(self, command):
        msg = "No such command: {0}".format(command)
        super(NoSuchCommand, self).__init__(msg)
        self.command = command
