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
    
    class mycli(CLI):    
        """
        Toplevel program - mycli
        """
        class State:
            version = '0.0.1'
        
        def normal_function(self, val):
            """Takes in data and outputs new data"""
            return "Josh"
    
    @command
    def greeting(cli, name="Hello"):
        """
        Prints "{name} World!"
        """
        print "{0} World!".format(name)

    class myhandler(Handler):
        """
        Organizational container of commands which can also add state variables
        """
        class State:
            version = '0.0.2'  # Handlers can have their own versioning
            cli = 'mycli'
    
        @command
        def hello(cli, data=None):
            """
            Prints "Hello, World!"
            """
            name = cli.normal_function(data)
            cli.greeting(name=name)

    if __name__ == "__main__":
        mycli.main()

Then on the commandline

.. code-block:: bash

    $ python mycli.py myhandler hello --data="Blah"
    > Josh World!
    $ #or if installed as a console script
    $ mycli myhandler hello --data="Blah"
    > Josh World!

Change Log

.. include:: ./ChangeLog
        :literal:
