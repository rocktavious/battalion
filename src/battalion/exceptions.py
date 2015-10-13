__all__ = ['NoSuchCommand']


class NoSuchCommand(ValueError):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)
        self.command = command
        self.supercommand = supercommand
