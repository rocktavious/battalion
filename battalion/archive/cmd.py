from .registry import registry

def command(*args, **kwargs):
    """
    Decorator that can expose a function as a command for a cli or handler
    """
    invoked = bool(not args or kwargs)
    if not invoked:
        func, args = args[0], ()

    def register(func):
        name = func.__name__
        cli = kwargs.get('cli', None)
        handler = kwargs.get('handler', None)
        if handler:
            key = (cli, handler)
        else:
            key = (cli,)
        aliases = kwargs.get('aliases', [])
        if not isinstance(aliases, list):
            raise ValueError('command decorator aliases takes a list, '
                             'just use "alias" for a single string alias!')
        alias = kwargs.get('alias', [])
        if isinstance(alias, list):
            aliases += alias
        else:
            aliases += [alias]
        registry.register(func, name, key, aliases)
        return func
    return register if invoked else register(func)