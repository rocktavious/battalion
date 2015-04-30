import re
from inspect import getargspec, getcallargs
from docopt import docopt, DocoptExit
from pyul.coreUtils import DotifyDict
from .registry import registry
from .exceptions import NoSuchCommand, CommandExtractionError


def get_command_args(command):
    args = [a for a in getargspec(command).args if a not in registry._fixtures.keys() and a != 'cli']
    return args


def get_command_spec(command, without_fixtures=True):
    spec = getargspec(command)
    positional = [None] * (len(spec.args) - len(spec.defaults or []))
    kwargs = getcallargs(command, *positional)
    kwargs.pop('cli')
    if without_fixtures:
        for name in registry._fixtures.keys():
            try:
                kwargs.pop(name)
            except KeyError:
                pass
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
        SystemExit(docstring)
    return cleanup_data(options)


def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]


def parse(docstring, args, key, docopt_kwargs={}):
    options = parse_argv(docstring, args, docopt_kwargs)
    command_name, args = options.pop('<command>'), options.pop('<args>')
    if command_name is None or command_name is False:
        raise CommandExtractionError(args)
    commands = registry.get_commands(key)
    handlers = registry.get_handlers(key)
    try:
        command = handlers[command_name]
    except KeyError:
        try:
            command = commands[command_name]
        except KeyError:
            raise NoSuchCommand(command_name, docstring)
    return options, command, args
