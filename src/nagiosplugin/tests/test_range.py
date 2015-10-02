from nagiosplugin.range import Range
import pytest


def test_empty_range_is_zero_to_infinity():
    r = Range('')
    assert r.invert is False
    assert r.start == 0
    assert r.end == float('inf')


def test_null_range():
    assert Range() == Range('')
    assert Range() == Range(None)


def test_explicit_start_end():
    r = Range('0.5:4')
    assert r.invert is False
    assert r.start == 0.5
    assert r.end == 4


def test_fail_if_start_gt_end():
    with pytest.raises(ValueError):
        Range('4:3')


def test_int():
    r = Range(42)
    assert r.invert is False
    assert r.start == 0
    assert r.end == 42


def test_float():
    r = Range(0.12)
    assert r.invert is False
    assert r.start == 0
    assert r.end == 0.12


def test_spec_with_unknown_type_should_raise():
    with pytest.raises(TypeError):
        Range([1, 2])


def test_omit_start():
    r = Range('5')
    assert r.invert is False
    assert r.start == 0
    assert r.end == 5


def test_omit_end():
    r = Range('7.7:')
    assert r.invert is False
    assert r.start == 7.7
    assert r.end == float('inf')


def test_start_is_neg_infinity():
    r = Range('~:5.5')
    assert r.invert is False
    assert r.start == float('-inf')
    assert r.end == 5.5


def test_invert():
    r = Range('@-9.1:2.6')
    assert r.invert is True
    assert r.start == -9.1
    assert r.end == 2.6


def test_range_from_range():
    orig = Range('@3:5')
    copy = Range(orig)
    assert copy == orig


def test_contains():
    r = Range('1.7:2.5')
    assert 1.6 not in r
    assert 1.7 in r
    assert 2.5 in r
    assert 2.6 not in r


def test_ne():
    assert Range("2:3") != Range("2:4")
    assert Range("2:3") != Range("1:3")
    assert Range("2:3") != Range("@2:3")


def test_repr():
    assert "Range('2:3')" == repr(Range('2:3'))


def test_empty():
    assert '' == str(Range())


def test_explicit_start_stop():
    assert '1.5:5' == str(Range('1.5:5'))


def test_str_omit_start():
    assert '6.7' == str('6.7')


def test_str_omit_end():
    assert '-6.5:' == str('-6.5:')


def test_neg_infinity():
    assert '~:-3.0' == str(Range('~:-3.0'))


def test_str_invert():
    assert '@3:7' == str(Range('@3:7'))


def test_large_number():
    assert '2800000000' == str(Range('2800000000'))
