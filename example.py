from battalion.command import CLI, Handler


class mycli(CLI):    
    """mycli

    Usage:
      mycli [options] COMMAND
      mycli -h|--help

    Options:
      --verbose                 Show more output
      --version                 Print version and exit

    Commands:
      myhandler     Example handler

    """
    version = '0.0.1'

class myhandler(Handler):
    """

    Usage:
      myhandler COMMAND

    Commands:
      hello     Example command
      greeting  Example options command

    """
    version = '0.0.1'
    cli = 'mycli'
    
    def hello(self):
        """
        Prints "Hello, World!"
    
        Usage:
          hello
    
        """
        print "Hello, World!"
        
    def greeting(self, name):
        """
        Prints "Hello, {name}"
    
        Usage:
          greeting [options]
          
        Options:
          -n --name NAME  The name of the person to greet
    
        """
        print "Hello, {0}!".format(name)

if __name__ == "__main__":
    mycli.main()