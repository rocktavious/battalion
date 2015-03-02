from battalion.command import CLI, Handler, command


class mycli(CLI):    
    """
    mycli
    """
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
    version = '0.0.2'
    cli = 'mycli'

    @command
    def hello(self):
        """
        Prints "Hello, World!"
        """
        print "Hello, World!"

    @command
    def greeting(self, greeting, name="World"):
        """
        Prints "Hello, {name}"
        """
        print "{0}, {1}!".format(greeting, name)

if __name__ == "__main__":
    mycli.main()