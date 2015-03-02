import re
from docopt import parse_argv, printable_usage, parse_defaults, parse_pattern, formal_usage, extras, AnyOptions, Option, Dict, TokenStream, DocoptExit

def parse_doc_section(name, source):
    pattern = re.compile('^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
                         re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]

# Custom override to docopt command to parse hierarchies of commands and fixup command args dict
def docopt(doc, argv=None, help=True, version=None, options_first=False):
    if argv is None:
        argv = sys.argv[1:]
    DocoptExit.usage = printable_usage(doc)
    options = parse_defaults(doc)
    pattern = parse_pattern(formal_usage(DocoptExit.usage), options)
    # [default] syntax for argument is disabled
    #for a in pattern.flat(Argument):
    #    same_name = [d for d in arguments if d.name == a.name]
    #    if same_name:
    #        a.value = same_name[0].value
    argv = parse_argv(TokenStream(argv, DocoptExit), list(options),
                      options_first)
    pattern_options = set(pattern.flat(Option))
    for ao in pattern.flat(AnyOptions):
        doc_options = parse_defaults(doc)
        ao.children = list(set(doc_options) - pattern_options)
        #if any_options:
        #    ao.children += [Option(o.short, o.long, o.argcount)
        #                    for o in argv if type(o) is Option]
    extras(help, version, argv, doc)
    matched, left, collected = pattern.fix().match(argv)
    if matched:  # better error message if left?
        args = Dict((a.name, a.value) for a in (pattern.flat() + collected))
        command_args = []
        for arg in left:
            if isinstance(arg, Option):
                command_args += [arg.name, arg.value]
            else:
                command_args += [arg.value]
        
        if command_args:
            args["COMMAND_ARGS"] = command_args    
        return args
    raise DocoptExit()