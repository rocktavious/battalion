import sys
from inspect import getdoc
from docopt import docopt, DocoptExit


class NoSuchCommand(ValueError):
    def __init__(self, command, supercommand):
        super(NoSuchCommand, self).__init__("No such command: %s" % command)

        self.command = command
        self.supercommand = supercommand


class Command(object):

    def docopt_options(self):
        return {'options_first': True}

    def parse(self, argv):
        docstring = getdoc(self)
        try:
            options = docopt(docstring,
                             argv,
                             **self.docopt_options())
        except DocoptExit:
            raise SystemExit(docstring)

        command = options['COMMAND']

        if command is None:
            raise SystemExit(getdoc(self))

        if not hasattr(self, command):
            raise NoSuchCommand(command, self)

        handler = getattr(self, command)
        handler_docstring = getdoc(handler)

        if handler_docstring is None:
            raise NoSuchCommand(command, self)

        try:
            command_options = docopt(handler_docstring,
                                     options['ARGS'],
                                     options_first=True)
        except DocoptExit:
            raise SystemExit(handler_docstring)

        return options, handler, command_options

    def finalize(self, command_options):
        return command_options

    def sys_dispatch(self):
        self.dispatch(sys.argv[1:])

    def dispatch(self, argv):
        self.run(*self.parse(argv))

    def run(self, options, handler, command_options):
        handler(*self.finalize(command_options))
