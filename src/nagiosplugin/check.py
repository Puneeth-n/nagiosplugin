"""Controller logic for check execution"""

from .context import Context, Contexts
from .error import CheckError
from .metric import Metric
from .resource import Resource
from .result import Result, Results
from .runtime import Runtime
from .state import Ok, Unknown
from .summary import Summary
import logging
import numbers
import sys

_log = logging.getLogger(__name__)


class Check(object):
    """Orchestrates the the various stages of check execution.

    When a check is called, it probes all resources and evaluates the
    returned metrics to results and performance data. A typical usage
    pattern would be to populate a check with domain objects and then
    delegate control to it. Interfacing with the outside system is done
    via a separate :class:`Runtime` object.
    """

    name = ''
    verbose = 1
    timeout = 10

    def __init__(self, *objects):
        """Initializes a :class:`Check` right away with `objects`. See
        :meth:`add` for a list of allowed object types.

        Alternatively, objects can be added later using the :meth:`add`
        method.
        """
        self.resources = []
        self.contexts = Contexts()
        self.summary = Summary()
        self.results = Results()
        self.perfdata = []
        self.add(*objects)

    def add(self, *objects):
        """Adds domain objects to a check.

        :param objects: one or more objects that are instances of
            :class:`~nagiosplugin.resource.Resource`,
            :class:`~nagiosplugin.context.Context`,
            :class:`~nagiosplugin.summary.Summary`, or
            :class:`~nagiosplugin.result.Results` or subclasses of one
            of these classes.
        """
        for obj in objects:
            if isinstance(obj, Resource):
                self.resources.append(obj)
                if self.name == '':
                    self.name = self.resources[0].name
            elif isinstance(obj, Context):
                self.contexts.add(obj)
            elif isinstance(obj, Summary):
                self.summary = obj
            elif isinstance(obj, Results):
                self.results = obj
            else:
                raise TypeError('cannot add type {0} to check'.format(
                    type(obj)), obj)
        return self

    def _evaluate_resource(self, resource):
        try:
            metric = None
            metrics = resource.probe()
            if not metrics:
                _log.warning('resource %s did not produce any metric',
                             resource.name)
            if isinstance(metrics, Metric):
                # resource returned a bare metric instead of list/generator
                metrics = [metrics]
            for metric in metrics:
                context = self.contexts[metric.context]
                metric = metric.replace(contextobj=context, resource=resource)
                self.results.add(metric.evaluate())
                self.perfdata.append(str(metric.performance() or ''))
        except CheckError as e:
            self.results.add(Result(Unknown, str(e), metric))

    def __call__(self):
        """Executes and populates :attr:`results` and :attr:`perfdata`.

        Don't call this method directly.  Instead invoke :meth:`main`,
        which delegates check execution to the :class:`Runtime`
        environment.
        """
        for resource in self.resources:
            self._evaluate_resource(resource)
        self.perfdata = sorted([p for p in self.perfdata if p])

    def set_verbose(self, verbose):
        """Parses either numerical or alphabetical verbosity specification.

        `verbose` can be an integer between 0 and 3 or a string like
        "v", "vv", or "vvv".

        .. versionadded:: 2.0
        """
        if verbose is None:
            return
        if isinstance(verbose, numbers.Number):
            self.verbose = int(verbose)
        else:
            self.verbose = len(verbose or [])

    def run(self, verbose=None, timeout=None):
        """Alternative main entry point that doesn't print output and exit.

        Initializes the runtime environment and runs the check under control of
        this runtime environment.

        This method does neither print the output to stdout nor exit the
        process. To get it all in one method, use :meth:`main` instead.

        :param verbose: output verbosity level between 0 and 3
        :param timeout: abort check execution with a :exc:`Timeout`
            exception after so many seconds (use 0 for no timeout)
        :return: (output, exitcode) tuple

        .. versionadded:: 2.0
        """

        self.set_verbose(verbose)
        if timeout is not None:
            self.timeout = int(timeout)
        runtime = Runtime()
        return runtime.execute(self)

    def main(self, verbose=None, timeout=None):  # pragma: no cover
        """Main entry point: execute check, print output, exit.

        Alternatively, use :meth:`run` if you want control output and
        exit actions from the calling function.

        :param verbose: output verbosity level between 0 and 3
        :param timeout: abort check execution with a :exc:`Timeout`
            exception after so many seconds (use 0 for no timeout)
        """
        output, exitcode = self.run(verbose, timeout)
        print(output, end='')
        sys.exit(exitcode)

    @property
    def state(self):
        """Overall check state.

        The most significant (=worst) state seen in :attr:`results` to
        far. :obj:`~nagiosplugin.state.Unknown` if no results have been
        collected yet. Corresponds with :attr:`exitcode`. Read-only
        property.
        """
        try:
            return self.results.most_significant_state
        except ValueError:
            return Unknown

    @property
    def summary_str(self):
        """Status line summary string.

        The first line of output that summarizes that situation as
        perceived by the check. The string is usually queried from a
        :class:`Summary` object. Read-only property.
        """
        if not self.results:
            return self.summary.empty() or ''
        elif self.state == Ok:
            return self.summary.ok(self.results) or ''
        return self.summary.problem(self.results) or ''

    @property
    def verbose_str(self):
        """Additional lines of output.

        Long text output if check runs in verbose mode. Also queried
        from :class:`~nagiosplugin.summary.Summary`. Read-only property.
        """
        return self.summary.verbose(self.results) or ''

    @property
    def exitcode(self):
        """Overall check exit code according to the Nagios API.

        Corresponds with :attr:`state`. Read-only property.
        """
        try:
            return int(self.results.most_significant_state)
        except ValueError:
            return 3
