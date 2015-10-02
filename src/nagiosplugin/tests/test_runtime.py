from nagiosplugin.runtime import Runtime, guarded
import logging
import nagiosplugin
import pytest


@pytest.fixture
def fake_check():

    class Check(object):
        summary_str = 'summary'
        verbose_str = 'long output'
        name = 'check'
        state = nagiosplugin.Ok
        exitcode = 0
        perfdata = None
        verbose = 2
        timeout = 20

        def __call__(self):
            pass

    return Check()


@pytest.fixture
def runtime_instance(fake_check):
    Runtime.instance = None
    r = Runtime()
    r.check = fake_check
    r.sysexit = lambda e: None
    return r


def test_runtime_is_singleton(runtime_instance):
    assert Runtime() is runtime_instance


def test_run_sets_exitcode(runtime_instance):
    runtime_instance.run()
    assert 0 == runtime_instance.exitcode


def test_execute_returns_output_and_exitcode(runtime_instance, fake_check):
    assert (('CHECK OK - summary\nlong output\n', 0) ==
            runtime_instance.execute(fake_check))


def test_verbose(runtime_instance):
    testcases = [(1, logging.WARNING),
                 (2, logging.INFO),
                 (3, logging.DEBUG)]
    for argument, exp_level in testcases:
        runtime_instance._configure_verbosity(argument)
        assert exp_level == runtime_instance.logchan.level


def _run_guarded_with_exception(exc):
    @guarded
    def main():
        raise exc
    main()


def test_handle_exception_should_output_and_exit(capsys, runtime_instance):

    def mock_exit(e):
        assert 3 == e
    runtime_instance.sysexit = mock_exit
    _run_guarded_with_exception(RuntimeError('problem'))
    assert 'UNKNOWN: RuntimeError: problem' in capsys.readouterr()[0]


def test_handle_exception_prints_no_traceback(runtime_instance, capsys):
    runtime_instance.check.verbose = 0
    _run_guarded_with_exception(RuntimeError('boom'))
    assert 'Traceback' not in '\n'.join(capsys.readouterr())


def test_handle_exception_verbose(runtime_instance, capsys):
    runtime_instance.check.verbose = 1
    _run_guarded_with_exception(RuntimeError('bang'))
    assert 'Traceback' in '\n'.join(capsys.readouterr())


def test_handle_timeout_exception(capsys):
    _run_guarded_with_exception(nagiosplugin.Timeout('1s'))
    assert ('UNKNOWN: Timeout: check execution aborted after 1s' in
            '\n'.join(capsys.readouterr()))


def test_dont_call_timeout_if_unset(monkeypatch, runtime_instance, fake_check):
    monkeypatch.setattr(nagiosplugin.runtime, 'with_timeout', pytest.fail)
    fake_check.timeout = 0
    runtime_instance.execute(fake_check)
