import sys
import pytest
import logging
from battalion.api import *
from battalion.exceptions import *


class DB(object):
    
    def __init__(self, state):
        self.msg = state.msg

    def myfunc(self):
        return self.msg


@fixture
def db(state):
    return DB(state)

@fixture(memoize=False)
def db2(state):
    return DB(state)

class acli(CLI):    
    """
    Toplevel program - acli
    """
    class State:
        version = '0.0.1'
        msg = ""

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

    @command(alias='greeting')
    def hello(cli, msg=None):
        """
        Prints "Hello World!"
        """
        name = cli.normal_function(data=msg)
        name = cli.myhandler.validate(data=name)
        cli.greeting(name=name)

class myhandler2(Handler):

    class State:
        cli = 'mycli'

    @command
    def logger(cli, msg):
        """
        Logs "{msg}"
        
        Options:
            -m --msg=<MSG>                      [default: None]
        """
        cli.log.info(msg)

@command(cli='mycli', alias='greet')
def multi_bind(cli, name="NAME"):
    """
    Prints {name}!
    """
    print name
    
registry.bind(multi_bind, 'mycli', 'myhandler2')
registry.bind(multi_bind, 'acli')


@pytest.fixture
def cli():
    return mycli()

def dispatch(cli, argv=None):
    try:
        return cli(argv)
    except SystemExit:
        return

def test_main(cli, capsys):
    rv = dispatch(cli, '--help')
    out, err = capsys.readouterr()
    assert cli.docstring in out

def test_version(cli, capsys):
    dispatch(cli, '--version')
    out, err = capsys.readouterr()
    assert '0.0.1' in out

def test_handler(cli, capsys):
    rv = cli.myhandler()
    out, err = capsys.readouterr()
    assert '' in out

def test_hello(cli, capsys):
    rv = dispatch(cli, 'myhandler hello Kyle')
    out, err = capsys.readouterr()
    assert 'Hello Kyle!' in out

def test_alias(cli, capsys):
    rv = dispatch(cli, 'myhandler greeting Kyle')
    out, err = capsys.readouterr()
    assert 'Hello Kyle!' in out

def test_nosuchcommand_exception(cli, capsys):
    rv = dispatch(cli, 'hello')
    out, err = capsys.readouterr()
    assert 'No such command: hello' in out

def test_logger(cli, caplog):
    rv = dispatch(cli, 'myhandler2 logger -mKyle')
    assert 'Kyle' in caplog.text()

def test_multi_bind(cli, capsys):
    rv = cli.myhandler2.multi_bind()
    out, err = capsys.readouterr()
    assert 'NAME' in out

if __name__ == "__main__":
    mycli.main()
