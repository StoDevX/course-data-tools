import sys
import os
import logging


def log(*args, **kwargs):
    logging.info(*args, file=sys.stderr, **kwargs)


def log_err(*args, **kwargs):
    logging.warning(*args, file=sys.stderr, **kwargs)
