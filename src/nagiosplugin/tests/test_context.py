from nagiosplugin.context import Context, ScalarContext, Contexts
import nagiosplugin
import unittest


class ContextTest(unittest.TestCase):

    def test_description_should_be_empty_by_default(self):
        c = Context('ctx')
        self.assertIsNone(c.describe(nagiosplugin.Metric('m', 0)))

    def test_fmt_template(self):
        m1 = nagiosplugin.Metric('foo', 1, 's', min=0)
        c = Context('describe_template', '{name} is {valueunit} (min {min})')
        self.assertEqual('foo is 1s (min 0)', c.describe(m1))

    def test_fmt_callable(self):
        def format_metric(metric, context, state):
            return '{0} formatted by {1}'.format(metric.name, context.name)

        m1 = nagiosplugin.Metric('foo', 1, 's', min=0)
        c = Context('describe_callable', fmt_metric=format_metric)
        self.assertEqual('foo formatted by describe_callable', c.describe(m1))

    def test_fmt_accepts_context_keyword(self):
        m1 = nagiosplugin.Metric('foo', 1, 's')
        c = Context('describe_template', '{name} range {context.range}')
        c.range = nagiosplugin.Range('3')
        self.assertEqual('foo range 3', c.describe(m1))


class ScalarContextTest(unittest.TestCase):

    def test_state_ranges_values(self):
        test_cases = [
            (1, nagiosplugin.Ok),
            (3, nagiosplugin.Warn),
            (5, nagiosplugin.Critical),
        ]
        c = ScalarContext('ctx', '1:2', '0:4')
        for value, exp_state in test_cases:
            m = nagiosplugin.Metric('time', value)
            self.assertEqual(nagiosplugin.Result(
                exp_state, 'time is {0}'.format(value), m),
                c.evaluate(m, None))

    def test_accept_none_warning_critical(self):
        c = ScalarContext('ctx')
        self.assertEqual(nagiosplugin.Range(), c.warning)
        self.assertEqual(nagiosplugin.Range(), c.critical)


class ContextsTest(unittest.TestCase):

    def test_keyerror(self):
        ctx = Contexts()
        ctx.add(Context('foo'))
        with self.assertRaises(KeyError):
            ctx['bar']

    def test_contains(self):
        ctx = Contexts()
        ctx.add(Context('foo'))
        self.assertTrue('foo' in ctx)
        self.assertFalse('bar' in ctx)

    def test_iter(self):
        ctx = Contexts()
        ctx.add(Context('foo'))
        # includes default contexts
        self.assertEqual(['default', 'foo', 'null'], sorted(list(ctx)))
