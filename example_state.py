from battalion.api import *
from battalion.log import enable_logging
from pprint import pprint

enable_logging('')

class mycli(CLI):    
    """
    Toplevel program - mycli
    """
    class State:
        version = '0.0.1'
        url = None
        options = [('--url=<URL>', 'The url for the thing')]

    @command
    def run_tests(cli, name):
        cli('test')
        cli('myhandler test')
        cli('myhandler2 test')

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
        options = [('--url2=<URL>', 'The url for the thing')]

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
    mycli()('test')