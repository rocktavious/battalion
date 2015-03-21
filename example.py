from battalion.api import *


class myCLI(CLI):    
    """
    Toplevel program - myCLI
    """
    class State:
        version = '0.0.1'
    
    def normal_function(self, val):
        return "Josh"

    @command
    def command_output(cli, val='test'):
        """"""
        return "Boom"

    @command
    def world(cli, name="Hello"):
        """
        Prints "{name} World!"
        """
        print "{0} World!".format(name)
        print cli
        

class myhandler(Handler):
    """
    Organizational container of commands which can also add state variables
    """
    class State:
        version = '0.0.2'  # Handlers can have their own versioning
        cli = 'myCLI'
        static_var = "Kyle"

    @command
    def hello(cli):
        """
        Prints "Hello, World!"
        """
        name = "Kyle"
        name = cli.normal_function(cli.state.static_var)
        name = cli.command_output(val=name)
        cli.myhandler.greeting(name=name)


@command(cli='myCLI', handler='myhandler', alias='greet') # alias or aliases are great ways to bridge gaps during refactoring of api
@command(cli='myCLI') # multiple command decorators can be applied to place a command into multiple areas for ease of use but still benefits from a single source of code
                      # NOTE: state will differ since its being built up with handler or without the handler
def greeting(cli, greeting="Hello", name="World"):
    """
    Prints "{greeting}, {name}"
    """
    print "{0}, {1}!".format(greeting, name)
    print cli.state.static_var

@command(cli='myCLI')
def test(cli, name="DAMN"):
    """
    Prints {name}!
    """
    print name
    
registry.bind(test, 'myCLI', 'myhandler')

if __name__ == "__main__":
    myCLI.main()