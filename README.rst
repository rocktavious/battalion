battalion
=========

.. image:: https://pypip.in/py_versions/battalion/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/battalion/

.. image:: https://pypip.in/license/battalion/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/battalion/

.. image:: https://pypip.in/download/battalion/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/battalion/

.. image:: https://pypip.in/version/battalion/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/battalion/

.. image:: https://pypip.in/wheel/battalion/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/battalion/

.. image:: https://requires.io/github/rocktavious/battalion/requirements.png?branch=master
        :target: https://requires.io/github/rocktavious/battalion/requirements/?branch=master
        :alt: Requirements Status

Python framework for commandline applications

Quickstart
----------

Feeling impatient? I like your style.

.. code-block:: bash

    $ pip install battalion

In mycli.py script:

.. code-block:: python

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

Then on the commandline

.. code-block:: bash

    $ python mycli.py myhandler hello
    > Hello World!
    $ #or if installed as a console script
    $ mycli myhandler hello
    > Hello World!
    $ #also
    $ mycli myhandler hello "Josh"
    > Hello Josh!
    $ mycli --help
    > Toplevel program - mycli
    > 
    > Usage:
    >     mycli [options] <command> [<args>...]
    >     mycli [options]
    > 
    > Options:
    >     -h, --help                     Show this screen.
    >     --version                      Show version.
    >     -d, --debug                    Show debug messages
    >     --config=<CONFIG>              The config filepath [default: ~/.mycli/mycli.yaml]
    > 
    > Commands:
    >     greeting                       Prints "Hello {name}!"
    >     myhandler                      Organizational container of commands which can also add state variables
    > 
    $ mycli myhandler hello --help
    > Prints "Hello World!"
    > 
    > Usage:
    >     hello [options]
    >     hello <msg> 
    > 
    > Options:
    >     --msg=<MSG>                      [default: None]
    > 