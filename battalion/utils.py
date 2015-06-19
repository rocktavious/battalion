import re
from inspect import getargspec, getcallargs
from docopt import docopt, DocoptExit
from pyul.coreUtils import DotifyDict
from .exceptions import NoSuchCommand, CommandExtractionError
from .registry import registry


def get_command_args(command):
    args = [a for a in getargspec(command).args if registry.is_fixture(a) is False and a != 'cli']
    return args


def get_command_spec(command):
    spec = getargspec(command)
    positional = [None] * (len(spec.args) - len(spec.defaults or []))
    kwargs = getcallargs(command, *positional)
    kwargs.pop('cli')
    return kwargs


def format_command_args(command, kwargs):
    new_kwargs = {}
    command_kwargs = get_command_spec(command)
    for k, v in sorted(kwargs.items()):
        k = cleanup_key(k)
        # check if arg
        if v is None or v == 'None':
            v = new_kwargs.get(k, None) or command_kwargs.get(k, None) or None
        if k in command_kwargs:
            new_kwargs[k] = v
    return new_kwargs


def cleanup_key(k):
    if k in ['<command>', '<args>']:
        return k
    if k.startswith('--'):
        k = k[2:]
    if k.startswith('-'):
        k = k[1:]
    k = k.replace('-', '_')
    k = k.replace('<', '')
    k = k.replace('>', '')
    return k


def cleanup_data(data):
    new_data = {}
    for k, v in data.items():
        k = cleanup_key(k)
        new_data[k] = True if v == 'True' else v
    return DotifyDict(new_data)


def parse_args(docstring, args, docopt_kwargs={}):
    try:
        options = docopt(docstring,
                         args,
                         **docopt_kwargs)
    except DocoptExit:
        options = {}
        SystemExit(docstring)
    return cleanup_data(options)


def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


def parse(docstring, args, handlers, commands, docopt_kwargs={}):
    options = parse_argv(docstring, args, docopt_kwargs)
    command_name, args = options.pop('<command>'), options.pop('<args>')
    if command_name is None or command_name is False:
        raise CommandExtractionError(args)
    try:
        command = handlers[command_name]
    except KeyError:
        try:
            command = commands[command_name]
        except KeyError:
            raise NoSuchCommand(command_name, docstring)
    return options, command, args
