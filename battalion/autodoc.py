import logging
from inspect import getdoc, cleandoc
from .base import Base
from .registry import registry
from .utils import get_command_args, get_command_spec

LOG = logging.getLogger(__name__)


class AutoDoc(Base):
    """
    Class that supports generating the docopt docstrings for the class and
    it's command functions.
    """
    class State:
        default_config = None
        column_padding = 30

    def __init__(self, *args, **kwargs):
        super(AutoDoc, self).__init__(*args, **kwargs)
        if self.__doc__ is None:
            self.__doc__ = """"""
        # We check if autodoc has already happened
        # so that test frameworks can keep generating new
        # instances of the same class without redocumenting
        # which would cause a failure
        if not hasattr(self, "__autodoc__"):
            self.generate_class_doc()
            self.generate_commands_doc()
            self.set_autodoc(self.docstring)

    @classmethod
    def set_autodoc(cls, docstring):
        cls.__autodoc__ = docstring

    @property
    def docstring(self):
        return self.__autodoc__

    def generate_class_doc(self):
        LOG.debug('Documenting %s', self._name)
        new_doc = getdoc(self) or """{0}""".format(self._name)
        new_doc += "\n\n"
        new_doc += self.generate_usage()
        new_doc += self.generate_options()
        new_doc += self.generate_commands()
        self.__autodoc__ = cleandoc(new_doc)

    def generate_commands_doc(self):
        for name, func in registry.get_handlers(self.key).items():
            LOG.debug('Documenting Handler %s', name)
            func()
        for name, func in registry.get_commands(self.key).items():
            LOG.debug('Documenting Command %s', name)
            new_command_doc = func.docstring if hasattr(func, 'docstring') else """{0}""".format(name)
            new_command_doc += "\n\n"
            new_command_doc += self.generate_command_usage(name, func)
            new_command_doc += self.generate_command_options(func)
            func.__autodoc__ = cleandoc(new_command_doc)

    def generate_usage(self):
        docstring = ""
        if "Usage:" not in self.__doc__:
            docstring += "Usage:\n"
            docstring += "    {0} [options] <command> [<args>...]\n".format(self.name)
            docstring += "    {0} [options]\n\n".format(self.name)
        return docstring

    def generate_options(self):
        if "Options:" not in self.__doc__:
            docstring = "Options:\n"
            for flags, desc in self.state.options:
                if flags == '--config=<CONFIG>' and flags not in docstring:
                    if registry.is_cli(self.key):
                        if self.state.default_config is None:
                            self.state.default_config = '~/.{name}/{name}.yaml'.format(name=self.name)
                        desc = desc.format(self.state.default_config)
                    else:
                        continue
                docstring += "    {0:<{2}} {1}\n".format(flags,
                                                         desc,
                                                         self.state.column_padding)
            docstring += "\n"
        return docstring

    def generate_commands(self):
        if "Commands:" not in self.__doc__:
            docstring = "Commands:\n"
            for k, v in registry.get_all(self.key).items():
                docstring += "    {0:<{2}} {1}\n".format(k,
                                                         getdoc(v),
                                                         self.state.column_padding)
            docstring += "\n"
        return docstring

    def generate_command_usage(self, name, command):
        docstring = ""
        if command.__doc__ is None or "Usage:" not in command.__doc__:
            docstring += "Usage:\n    {0} [options]\n".format(name)
            args = get_command_args(command)
            spec = get_command_spec(command)
            if args:
                docstring += "    {0} ".format(name)
                for arg_name in args:
                    if spec[arg_name] is not None:
                        docstring += "[<{0}>] ".format(arg_name)
                    else:
                        docstring += "<{0}> ".format(arg_name)
                docstring += "\n"
            docstring += "\n"
        return docstring

    def generate_command_options(self, command):
        docstring = ""
        if command.__doc__ is None or "Options:" not in command.__doc__:
            args = get_command_spec(command)
            if args:
                docstring += "Options:\n"
                for arg, default in args.items():
                    flag_def = "--{0}=<{1}>".format(arg,
                                                    arg.upper())
                    docstring += "    {0:<{3}} {1} [default: {2}]\n".format(flag_def,
                                                                            ' ',
                                                                            default,
                                                                            self.state.column_padding)
                docstring += "\n"
        return docstring
