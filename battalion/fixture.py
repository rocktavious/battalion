from functools import wraps
from .registry import registry


def doublewrap(f):
    '''
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    '''
    @wraps(f)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return f(args[0])
        else:
            # decorator arguments
            return lambda realf: f(realf, *args, **kwargs)

    return new_dec


@doublewrap
def fixture(func, memoize=True):
    """
    Decorator for a function that will be called ahead of the execution
    of a command that provides a return value to fill the commands
    argument with

    Fixtures memoize their results by default.
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        cache = func.cache  # attributed added by memoize
        if func in cache:
            return cache[func]
        else:
            cache[func] = result = func(*args, **kwargs)
            return result
    if memoize:
        func.cache = {}
        new_func = wrap
    else:
        new_func = func
    registry.register_fixture(new_func, func.__name__)
    return new_func