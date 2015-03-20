from battalion.api import CLI, Handler, command, registry


class myCLI(CLI):    
    """
    Toplevel program - myCLI
    """
    class State:
        version = '0.0.1'

    @command
    def world(state, name="Hello"):
        """
        Prints "{name} World!"
        """
        print "{0} World!".format(name)
        

class myhandler(Handler):
    """
    Organizational container of commands that also passes `options` to all commands
    but does not inherit options from the CLI
    """
    class State:
        version = '0.0.2'  # Handlers can have their own versioning
        cli = 'myCLI'
        static_var = "Kyle"

    @command
    def hello(state):
        """
        Prints "Hello, World!"
        """
        print "Hello, World!"


@command(cli='myCLI', handler='myhandler', alias='greet') # alias or aliases are great ways to bridge gaps during refactoring of api
@command(cli='myCLI') # multiple command decorators can be applied to place a command into multiple areas for ease of use but still benefits from a single source of code
                      # NOTE: state will differ since its being built up with handler or without the handler
def greeting(state, greeting="Hello", name="World"):
    """
    Prints "{greeting}, {name}"
    """
    print "{0}, {1}!".format(greeting, name)
    print state.static_var

@command(cli='myCLI')
def test(state, name="DAMN"):
    """
    Prints {name}!
    """
    print name
    
registry.bind(test, 'myCLI', 'myhandler')

if __name__ == "__main__":
    myCLI.main()