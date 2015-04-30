__all__ = ['NoSuchCommand', 'CommandExtractionError']

class CommandExtractionError(ValueError):
    def __init__(self, argv):
        msg = "Unable to extract command from: {0}".format(argv)
        super(CommandExtractionError, self).__init__(msg)
        self.argv = argv

class NoSuchCommand(ValueError):
    def __init__(self, command_name, docstring):
        msg = "No such command: {0}".format(command_name)
        super(NoSuchCommand, self).__init__(msg)
        self.command_name = command_name
        self.docstring = docstring
