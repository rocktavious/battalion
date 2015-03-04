from battalion.api import CLI, Handler, command, registry


class myCLI(CLI):    
    """
    Toplevel program - myCLI
    """
    class State:
        version = '0.0.1'
        options = [('--config=<CONFIG>', 'The config filepath [default: ~/.mycli/mycli.cfg]')]

    @command
    def world(options, name="Hello"):
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

    @command
    def hello(options):
        """
        Prints "Hello, World!"
        """
        print "Hello, World!"


@command(cli='myCLI', handler='myhandler', alias='greet') # alias or aliases are great ways to bridge gaps during
@command(cli='myCLI') # multiple command decorators can be applied to place a command into multiple areas for ease of use but still benefits from a single source of code
                      # NOTE: options will differ since its either the handler passing the options or the CLI passing the options
def greeting(options, greeting="Hello", name="World"):
    """
    Prints "{greeting}, {name}"
    """
    print "{0}, {1}!".format(greeting, name)
    print options

@command(cli='myCLI')
def test(options, name="DAMN"):
    """
    Prints {name}!
    """
    print name
    
registry.bind(test, 'myCLI', 'myhandler')

if __name__ == "__main__":
    myCLI.main()