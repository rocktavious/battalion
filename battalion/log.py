import logging

logging_setup = False

SIMPLE = "[%(levelname)s] %(message)s"
VERBOSE = "%(levelname)-6s %(asctime)s line:%(levelno)-3d %(name)-25s  | %(message)s"


def enable_logging(root_logger_name, fmt=SIMPLE, level=logging.DEBUG):
    global logging_setup

    if not logging_setup:
        logging.basicConfig(format=fmt,
                            datefmt="%d-%m %H:%M:%S",
                            level=level)
        logging_setup = True
        for handler in logging.root.handlers:
            handler.addFilter(logging.Filter(root_logger_name))
