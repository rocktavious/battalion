from battalion.api import *

# This represents a heavyweight obj that takes a while to be instantiated
class Obj():
    
    def __init__(self, state):
        self.state = state

    def data(self):
        return self.state.msg


# Fixtures allow you to wrap up objects to be based to commands at runtime
# This is great for lazy object creation and / or only instantiating an object
# just in time for when its needed  -  This is very similar to how pytest
# fixtures work
@fixture
def obj(state):
    # If you control the object you can have the object configure itself from
    # the state object, or you can instantiate the object and configure it 
    # right here before you return it
    return Obj(state)


class cli(CLI):    
    """
    Toplevel program - cli
    """
    class State:
        version = '0.0.1'
        options = [('--msg=<MSG>', 'The message [default: BOOM!]')]
        msg = "BOOM!" # if given by the user as an option this will be overridden
    
    def normal_function(self, val):
        return "Josh"

    @command
    def command_output(obj, val=None):
        return val or obj.data()

    @command
    def add(cli, num1, num2, mul=2):
        """
        Add {num1} to {num2}
        """
        return (float(num1) + float(num2)) * float(mul)


class handler(Handler):
    """
    Organizational container of commands which can also add state variables
    """
    class State:
        version = '0.0.2'  # Handlers can have their own versioning
        cli = 'cli'
        options = [('--url=<URL>', 'The url for the thing')]
        static_var = "Kyle"
        url = 'http://google.com'

    @command
    def hello(cli):
        """
        Prints "Hello, World!"
        """
        name = cli.normal_function(cli.state.static_var)
        name = cli.command_output(val=name)
        cli.myhandler.greeting(name=name)

    @command(alias='add2')
    def add(cli, num1, num2):
        """
        Add {num1} to {num2}
        """
        return cli.main(['add', num1, num2])


@command(cli='myCLI', handler='myhandler', alias='greet') # alias or aliases are great ways to bridge gaps during refactoring of api
@command(cli='myCLI') # multiple command decorators can be applied to place a command into multiple areas for ease of use but still benefits from a single source of code
                      # NOTE: state will differ since its being built up with handler or without the handler
def greeting(state, name="World"):
    """
    Prints "{greeting}, {name}"
    """
    print "Hello {0}!".format(name)
    print state


def test_url(state):
    """
    Prints {name}!
    """
    print state.url
    
registry.bind(test_url, 'myCLI', 'myhandler')

if __name__ == "__main__":
    cli.main(['--help'])
    cli.main(['command_output', '--help'])
    cli.main(['handler', '--help'])
    cli.main(['command_output'])
    cli.main(['command_output', "Bash!"])
    cli.main(['--msg', 'BOYAH!', 'command_output'])
    cli.main(['greeting'])
    cli.main(['handler', 'greeting'])
    cli.main(['plus', '2', '3'])
    cli.main(['handler', 'plus', '2', '3'])
    cli.main(['handler', '--url', 'BOOM', 'test_url'])
    cli.main(['handler', 'test_url'])
    cli.main(['--dryrun', 'myhandler', 'hello'])
    cli.main(['handler', 'hello'])