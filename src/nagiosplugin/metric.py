"""Structured representation for data points.

This module contains the :class:`Metric` class whose instances are
passed as value objects between most of nagiosplugin's core classes.
Typically, :class:`~.resource.Resource` objects emit a list of metrics
as result of their :meth:`~.resource.Resource.probe` methods.
"""

import copy
import numbers
import warnings


class Metric(object):
    """Single measured value.

    The value should be expressed in terms of base units, so
    Metric('swap', 10240, 'B') is better than Metric('swap', 10, 'kiB').
    """

    def __init__(self, name, value, uom=None, min=None, max=None, context=None,
                 contextobj=None, resource=None):
        """Creates new Metric instance.

        :param name: short internal identifier for the value -- appears
            also in the performance data
        :param value: data point, usually has a boolen or numeric type,
            but other types are also possible
        :param uom: :term:`unit of measure`, preferrably as ISO
            abbreviation like "s"
        :param min: minimum value or None if there is no known minimum
        :param max: maximum value or None if there is no known maximum
        :param context: name of the associated context (defaults to the
            metric's name if left out)
        :param contextobj: reference to the associated context object
            (set automatically by :class:`~nagiosplugin.check.Check`)
        :param resource: reference to the originating
            :class:`~nagiosplugin.resource.Resource` (set automatically
            by :class:`~nagiosplugin.check.Check`)
        """
        self.name = name
        self.value = value
        self.uom = uom
        self.min = min
        self.max = max
        self.context = context or name
        self.contextobj = contextobj
        self.resource = resource

    def __str__(self):
        """Same as :attr:`valueunit`."""
        return self.valueunit

    def replace(self, **attr):
        """Creates new instance with updated attributes."""
        new = copy.copy(self)
        new.__dict__.update(attr)
        return new

    @property
    def description(self):
        """Human-readable, detailed string representation.

        Delegates to the :class:`~.context.Context` to format the value.

        :returns: :meth:`~.context.Context.describe` output or
            :attr:`valueunit` if no context has been associated yet

        .. deprecated:: 1.3
           Don't use :meth:`description` anymore; instead use/override
           :meth:`~.context.Context.describe` and
           :meth:`~.context.Context.evaluate` directly.
        """
        warnings.warn('Metric.description is deprecated; use '
                      'Context.describe() instead', DeprecationWarning)
        return str(self)

    @property
    def valueunit(self):
        """Compact string representation.

        This is just the value and the unit. If the value is a real
        number, express the value with a limited number of digits to
        improve readability.
        """
        return '%s%s' % (self._human_readable_value, self.uom or '')

    @property
    def _human_readable_value(self):
        """Limit number of digits for floats."""
        if (isinstance(self.value, numbers.Real) and
                not isinstance(self.value, numbers.Integral)):
            return '%.4g' % self.value
        return str(self.value)

    def evaluate(self):
        """Evaluates this instance according to the context with the
        matching name.

        :return: :class:`~nagiosplugin.result.Result` object
        :raise RuntimeError: if no context has been associated yet
        """
        if not self.contextobj:
            raise RuntimeError('no context set for metric', self.name)
        return self.contextobj.evaluate(self, self.resource)

    def performance(self):
        """Generates performance data according to the context.

        :return: :class:`~nagiosplugin.performance.Performance` object
        :raise RuntimeError: if no context has been associated yet
        """
        if not self.contextobj:
            raise RuntimeError('no context set for metric', self.name)
        return self.contextobj.performance(self, self.resource)
