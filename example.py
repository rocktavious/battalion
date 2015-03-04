from battalion.api import CLI, Handler, command


class mycli(CLI):    
    """
    mycli
    """
    class State:
        version = '0.0.1'

    @command
    def world(self, name="Hello"):
        """
        Prints "{name} World!"
        """
        print "{0} World!".format(name)
        

class myhandler(Handler):
    """
    myhandler
    """
    class State:
        version = '0.0.2'
        cli = 'mycli'
        
    def __init__(self):
        super(myhandler, self).__init__()

    @command
    def hello(self):
        """
        Prints "Hello, World!"
        """
        print "Hello, World!"

    @command
    def greeting(self, greeting="Hello", name="World"):
        """
        Prints "{greeting}, {name}"
        """
        print "{0}, {1}!".format(greeting, name)

if __name__ == "__main__":
    mycli.main()