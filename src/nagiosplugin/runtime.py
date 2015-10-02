"""Functions and classes to interface with the system.

This module contains the :class:`Runtime` class that handles exceptions,
timeouts and logging. Plugin authors should not use Runtime directly,
but decorate the plugin's main function with :func:`~.runtime.guarded`.
"""

from .output import Output
from .error import Timeout
from .platform import with_timeout
import io
import logging
import sys
import functools
import traceback


def guarded(func):
    """Runs a function in a newly created runtime environment.

    A guarded function behaves correctly with respect to the Nagios
    plugin API if it aborts with an uncaught exception or a
    timeout. It exits with an *unknown* exit code and prints a traceback
    in a format acceptable by Nagios.

    This function should be used as a decorator for the plugin's `main`
    function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        runtime = Runtime()
        try:
            return func(*args, **kwds)
        except Timeout as exc:
            runtime._handle_exception(
                'Timeout: check execution aborted after {0}'.format(exc))
        except Exception:
            runtime._handle_exception()
    return wrapper


class Runtime(object):
    """Singleton which handles output, logging and exceptions."""

    instance = None
    check = None
    logchan = None
    output = None
    exitcode = 70  # EX_SOFTWARE
    sysexit = sys.exit

    def __new__(cls):
        if not cls.instance:
            cls.instance = super(Runtime, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        rootlogger = logging.getLogger(__name__.split('.', 1)[0])
        rootlogger.setLevel(logging.DEBUG)
        if not self.logchan:
            self.logchan = logging.StreamHandler(io.StringIO())
            self.logchan.setFormatter(logging.Formatter('%(message)s'))
            rootlogger.addHandler(self.logchan)
        if not self.output:
            self.output = Output(self.logchan)

    def _handle_exception(self, statusline=None):
        exc_type, value = sys.exc_info()[0:2]
        name = self.check.name.upper() + ' ' if self.check else ''
        self.output.status = '{0}UNKNOWN: {1}'.format(
            name, statusline or traceback.format_exception_only(
                exc_type, value)[0].strip())
        if not self.check or self.check.verbose > 0:
            self.output.add_longoutput(traceback.format_exc())
        print(self.output, end='')
        self.sysexit(3)

    def _configure_verbosity(self, verbose):
        if verbose >= 3:
            self.logchan.setLevel(logging.DEBUG)
        elif verbose == 2:
            self.logchan.setLevel(logging.INFO)
        else:
            self.logchan.setLevel(logging.WARNING)
        self.output.verbose = verbose

    def run(self):
        self.check()
        self.output.add(self.check)
        self.exitcode = self.check.exitcode

    def execute(self, check):
        """Execute `check` with timeout guard and output wrapper.

        :param verbose: sets logging level
        :param timeout: aborts execution after `timeout` seconds
        :return: tuple (output, exitcode)
        """
        self.check = check
        self._configure_verbosity(check.verbose)
        if check.timeout > 0:
            with_timeout(check.timeout, self.run)
        else:
            self.run()
        return str(self.output), self.exitcode
