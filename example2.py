from battalion.api import *

class myCLI(CLI):    
    """
    Toplevel program - myCLI
    """
    class State:
        version = '0.0.1'

    @command
    def hello(cli, name="Hello"):
        """
        Prints "{name} World!"
        """
        cli.log.info("{0} World!".format(name))
        

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
        cli.log.info("Hello")


if __name__ == "__main__":
    myCLI.main()