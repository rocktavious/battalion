from battalion.api import *


class DB(object):
    
    def __init__(self, state):
        self.msg = state.git_msg

    def myfunc(self):
        return self.msg


@fixture
def db(state):
    return DB(state)


class mycli(CLI):    
    """
    Toplevel program - mycli
    """
    class State:
        version = '0.0.1'
        msg = ""

    @command
    def normal_function(cli, db, data=None):  # NOTE: the "db" arg will be populated from the "db" fixture function
        """Takes in data and outputs new data"""
        if data is None:
            return db.myfunc()
        else:
            return data

    @command
    def greeting(cli, name="Hello"):
        """
        Prints "Hello {name}!"
        """
        print "Hello {0}!".format(name)


class myhandler(Handler):
    """
    Organizational container of commands which can also add state variables
    """
    class State:
        version = '0.0.2'  # Handlers can have their own versioning
        cli = 'mycli'
        msg = "World"

    @command
    def validate(cli, data):
        return data

    @command
    def hello(cli, msg=None):
        """
        Prints "Hello World!"
        """
        name = cli.normal_function(data=msg)
        name = cli.myhandler.validate(data=name)
        cli.greeting(name=name)


if __name__ == "__main__":
    mycli.main()