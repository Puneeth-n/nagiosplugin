"""Metadata about metrics to perform data :term:`evaluation`.

This module contains the :class:`Context` class, which is the base for
all contexts. :class:`ScalarContext` is an important specialization to
cover numeric contexts with warning and critical thresholds. The
:class:`~.check.Check` controller selects a context for each
:class:`~.metric.Metric` by matching the metric's `context` attribute with the
context's `name`. The same context may be used for several metrics.

Plugin authors may just use to :class:`ScalarContext` in the majority of cases.
Sometimes is better to subclass :class:`Context` instead to implement custom
evaluation or performance data logic.
"""

from .performance import Performance
from .range import Range
from .result import Result
from .state import Ok, Warn, Critical


class Context(object):

    def __init__(self, name, fmt_metric=None, result_cls=Result):
        """Creates generic context identified by `name`.

        Generic contexts just format associated metrics and evaluate
        always to :obj:`~nagiosplugin.state.Ok`. Metric formatting is
        controlled with the :attr:`fmt_metric` attribute. It can either
        be a string or a callable. See the :meth:`describe` method for
        how formatting is done.

        :param name: context name that is matched by the context
            attribute of :class:`~nagiosplugin.metric.Metric`
        :param fmt_metric: string or callable to convert
            context and associated metric to a human readable string
        :param result_cls: use this class (usually a
            :class:`~.result.Result` subclass) to represent the
            evaluation outcome
        """
        self.name = name
        self.fmt_metric = fmt_metric
        self.result_cls = result_cls

    def evaluate(self, metric, resource):
        """Determines state of a given metric.

        This base implementation returns :class:`~nagiosplugin.state.Ok`
        in all cases. Plugin authors may override this method in
        subclasses to specialize behaviour.

        :param metric: associated metric that is to be evaluated
        :param resource: resource that produced the associated metric
            (may optionally be consulted)
        :returns: :class:`~.result.Result` object
        """
        return self.result_cls(Ok, self.describe(metric), metric)

    def performance(self, metric, resource):
        """Derives performance data from a given metric.

        This base implementation just returns none. Plugin authors may
        override this method in subclass to specialize behaviour.

        :param metric: associated metric from which performance data are
            derived
        :param resource: resource that produced the associated metric
            (may optionally be consulted)
        :returns: :class:`Perfdata` object or `None`
        """
        return None

    def describe(self, metric, state=None):
        """Provides human-readable metric description.

        Formats the metric according to the :attr:`fmt_metric`
        attribute. If :attr:`fmt_metric` is a string, it is evaluated as
        format string (see below).  If :attr:`fmt_metric` is callable,
        it should return the formatted string and is called as follows::

            fmt_metric(metric, context, state)

        If :attr:`fmt_metric` is not set, this default implementation
        does not return a description.

        Available fmt_metric keywords:
           * all metric attributes in the root namespace (like `name`,
             `value`, ...)
           * all context attributes in the `context` namespace (like
             `context.myattribute`).

        :param metric: associated metric
        :returns: description string or None
        """
        if not self.fmt_metric:
            return
        if hasattr(self.fmt_metric, '__call__'):
            return self.fmt_metric(metric, self, state)
        else:
            return self.fmt_metric.format(
                name=metric.name, value=metric.value, uom=metric.uom,
                valueunit=metric.valueunit, min=metric.min, max=metric.max,
                context=self)


class ScalarContext(Context):

    def __init__(self, name, warning=None, critical=None,
                 fmt_metric='{name} is {valueunit}', result_cls=Result):
        """Ready-to-use :class:`Context` subclass for scalar values.

        ScalarContext models the common case where a single scalar is to
        be evaluated against a pair of warning and critical thresholds.

        :attr:`name`, :attr:`fmt_metric`, and :attr:`result_cls`,
        are described in the :class:`Context` base class.

        :param warning: Warning threshold as
            :class:`~nagiosplugin.range.Range` object or range string.
        :param critical: Critical threshold as
            :class:`~nagiosplugin.range.Range` object or range string.
        """
        super(ScalarContext, self).__init__(name, fmt_metric, result_cls)
        self.warning = Range(warning)
        self.critical = Range(critical)

    def evaluate(self, metric, resource):
        """Compares metric with ranges and determines result state.

        The metric's value is compared to the instance's :attr:`warning`
        and :attr:`critical` ranges, yielding an appropropiate state
        depending on how the metric fits in the ranges. Plugin authors
        may override this method in subclasses to provide custom
        evaluation logic.

        :param metric: metric that is to be evaluated
        :param resource: not used
        :returns: :class:`~nagiosplugin.result.Result` object
        """
        if not self.critical.match(metric.value):
            state = Critical
        elif not self.warning.match(metric.value):
            state = Warn
        else:
            state = Ok
        hint = self.describe(metric, state)
        return self.result_cls(state, hint, metric)

    def performance(self, metric, resource):
        """Derives performance data.

        The metric's attributes are combined with the local
        :attr:`warning` and :attr:`critical` ranges to get a
        fully populated :class:`~nagiosplugin.performance.Performance`
        object.

        :param metric: metric from which performance data are derived
        :param resource: not used
        :returns: :class:`~nagiosplugin.performance.Performance` object
        """
        return Performance(metric.name, metric.value, metric.uom,
                           self.warning, self.critical,
                           metric.min, metric.max)


class Contexts:
    """Container for collecting all generated contexts."""

    def __init__(self):
        self.by_name = dict(
            default=ScalarContext('default', '', ''),
            null=Context('null'))

    def add(self, context):
        self.by_name[context.name] = context

    def __getitem__(self, context_name):
        try:
            return self.by_name[context_name]
        except KeyError:
            raise KeyError('cannot find context', context_name,
                           'known contexts: {0}'.format(
                               ', '.join(self.by_name.keys())))

    def __contains__(self, context_name):
        return context_name in self.by_name

    def __iter__(self):
        return iter(self.by_name)
