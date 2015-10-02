from nagiosplugin.performance import Performance
import pytest


def test_normal_label():
    assert 'd=10' == str(Performance('d', 10))


def test_label_quoted():
    assert "'d d'=10" == str(Performance('d d', 10))


def test_label_must_not_contain_quotes():
    with pytest.raises(RuntimeError):
        str(Performance("d'", 10))


def test_label_must_not_contain_equals():
    with pytest.raises(RuntimeError):
        str(Performance("d=", 10))
