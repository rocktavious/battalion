from battalion.api import *
from battalion.log import enable_logging
from pprint import pprint

class mycli(CLI):    
    """
    Toplevel program - mycli
    """
    class State:
        version = '0.0.1'
        url = None
        options = [('--url=<URL>', 'The url for the thing'),
                   ('--bool', 'Should Print True [default: True]')]

    @command
    def run_tests(cli, name):
        cli('test')
        cli('myhandler test')
        cli('myhandler2 test')

    @command
    def test2(cli):
        print cli.state.bool

    @command
    def test(cli):
        print cli.state.mycli
        print cli.state.myhandler
        cli('myhandler test')


class myhandler(Handler):
    """
    Organizational container of commands which can also add state variables
    """
    class State:
        version = '0.0.2'  # Handlers can have their own versioning
        cli = 'mycli'
        static_var = "Kyle"
        url = 'http://google.com'
        options = [('--url=<URL>', 'The url for the thing')]
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

    @command
    def test(cli):
        print cli.state.mycli
        print cli.state.myhandler

class myhandler2(Handler):
    """
    Organizational container of commands which can also add state variables
    """
    class State:
        version = '0.0.3'  # Handlers can have their own versioning
        cli = 'mycli'
        url = 'http://maps.google.com'

    @command
    def test(cli):
        print cli.state.myhandler
        print cli.state.myhandler2


if __name__ == "__main__":
    mycli()('test2')