from nagiosplugin.metric import Metric
import pytest
import warnings


def test_valueunit_float():
    assert '1.302s' == Metric('time', 1.30234876, 's').valueunit


def test_valueunit_scientific():
    assert '1.3e+04s' == Metric('time', 13000., 's').valueunit


def test_valueunit_should_not_use_scientific_for_large_ints():
    assert '13000s' == Metric('time', 13000, 's').valueunit


def test_valueunit_nonfloat():
    assert 'text' == Metric('text', 'text').valueunit


def test_evaluate_fails_if_no_context():
    with pytest.raises(RuntimeError):
        Metric('time', 1, 's').evaluate()


def test_performance_fails_if_no_context():
    with pytest.raises(RuntimeError):
        Metric('time', 1, 's').performance()


def test_description_should_issue_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        Metric('time', 12800, 's').description
        assert 1 == len(w)
        assert w[0].category is DeprecationWarning
