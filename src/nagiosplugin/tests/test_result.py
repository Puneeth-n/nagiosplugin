from nagiosplugin.result import Result, Results
from nagiosplugin.state import Ok, Warn, Critical, Unknown
import nagiosplugin
import pytest


def test_resorce_should_be_none_for_resourceless_metric():
    assert Result(Ok).resource is None


def test_metric_resorce():
    res = object()
    m = nagiosplugin.Metric('foo', 1, resource=res)
    assert Result(Ok, metric=m).resource == res


def test_eq():
    m = nagiosplugin.Metric('foo', 1)
    assert Result(Ok, 'hint', m) == Result(Ok, 'hint', m)


def test_ne():
    m1 = nagiosplugin.Metric('foo', 1)
    m2 = nagiosplugin.Metric('foo', 2)
    for left, right in (
            (Result(Ok, 'hint', m1), Result(Critical, 'hint', m1)),
            (Result(Ok, 'hint 1', m1), Result(Ok, 'hint 2', m1)),
            (Result(Ok, 'hint', m1), Result(Ok, 'hint', m2))):
        assert left != right


def test_context_should_be_none_for_contextless_metric():
    assert Result(Ok).context is None


def test_metric_context():
    ctx = object()
    m = nagiosplugin.Metric('foo', 1, contextobj=ctx)
    assert Result(Ok, metric=m).context == ctx


def test_str_metric_with_hint():
    assert 'unexpected' == str(Result(Warn, 'unexpected',
                                      nagiosplugin.Metric('foo', 2)))


def test_str_metric_only():
    assert '3' == str(Result(Warn, metric=nagiosplugin.Metric('foo', 3)))


def test_str_hint_only():
    assert 'how come?' == str(Result(Warn, 'how come?'))


def test_str_empty_hint():
    assert '' == str(Result(Warn, '', nagiosplugin.Metric('foo', 4)))


def test_str_empty():
    assert '' == str(Result(Warn))


def test_lookup_by_metric_name():
    r = Results()
    result = Result(Ok, '', nagiosplugin.Metric('met1', 0))
    r.add(result, Result(Ok, 'other'))
    assert r['met1'] == result


def test_lookup_by_index():
    r = Results()
    result = Result(Ok, '', nagiosplugin.Metric('met1', 0))
    r.add(Result(Ok, 'other'), result)
    assert r[1] == result


def test_len():
    r = Results()
    r.add(Result(Ok), Result(Ok), Result(Ok))
    assert 3 == len(r)


def test_iterate_in_order_of_descending_states():
    r = Results()
    r.add(Result(Warn), Result(Ok), Result(Critical), Result(Warn))
    assert [Critical, Warn, Warn, Ok] == [result.state for result in r]


def test_most_significant_state_shoud_raise_valueerror_if_empty():
    with pytest.raises(ValueError):
        Results().most_significant_state


def test_most_significant_state():
    r = Results()
    r.add(Result(Ok))
    assert Ok == r.most_significant_state
    r.add(Result(Critical))
    assert Critical == r.most_significant_state
    r.add(Result(Warn))
    assert Critical == r.most_significant_state


def test_most_significant_should_return_empty_set_if_empty():
    assert [] == Results().most_significant


def test_most_signigicant():
    r = Results()
    r.add(Result(Ok), Result(Warn), Result(Ok), Result(Warn))
    assert [Warn, Warn] == [result.state for result in r.most_significant]


def test_first_significant():
    r = Results()
    r.add(Result(Critical), Result(Unknown, 'r1'), Result(Unknown, 'r2'),
          Result(Ok))
    assert Result(Unknown, 'r1') == r.first_significant


def test_contains():
    results = Results()
    r1 = Result(Unknown, 'r1', nagiosplugin.Metric('m1', 1))
    results.add(r1)
    assert 'm1' in results
    assert 'm2' not in results


def test_add_in_init():
    results = Results(Result(Unknown, 'r1'), Result(Unknown, 'r2'))
    assert 2 == len(results)


def test_add_should_fail_unless_result_passed():
    with pytest.raises(ValueError):
        Results(True)
