import time
from battalion.api import *

class Git():
    
    def __init__(self, state):
        time.sleep(5)
        self.msg = state.git_msg

    def myfunc(self):
        print self.msg

@fixture
def git(state):
    return Git(state)

class myCLI(CLI):    
    """
    Toplevel program - myCLI
    """
    class State:
        version = '0.0.1'
        git_msg = "WOW1"

    @command
    def hello(cli, git, name="Hello"):
        """
        Prints "{name} World!"
        """
        cli.log.info("{0} World!".format(name))
        git.myfunc()
        cli.log.info("Fixture: {0}".format(git))
        cli.hello2(name='MYVALUE')

    @command
    def hello2(cli, git, name="Hello"):
        """
        Prints "{name} World!"
        """
        cli.log.info("{0} World!".format(name))
        git.myfunc()
        cli.log.info("Fixture: {0}".format(git))


if __name__ == "__main__":
    myCLI.main()