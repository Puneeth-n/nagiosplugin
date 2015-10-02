.. _tips_and_tricks:

Tips and Tricks
===============

Must each metric have its own context?
--------------------------------------

In general, no. It is just the default that each metric looks for its own
context. Sometimes it is easier to use the same context for multiple
metrics. For example, if you want to monitor a number of file systems and check
if any of these is more than 90% full, use the same context for all metrics::

   def probe(self):
      ...
      return Metric(..., context='disk')

Distinct context are required if you have differing evaluation criteria or
differing output formatting requirements.


How to create contexts dynamically during probe execution
---------------------------------------------------------

Sometimes there is no point in separating resource discovery and metrics
acquisition as everything comes from a single system operation. The
problem here is that nagiosplugin expects the resources and contexts being
created before probing starts --- `~nagiosplugin.resource.Resource` and
`~nagiosplugin.context.Context` must be added in the outer scope. If this is not
possible, create a single super-resource and pass the check object to it::

   class MyResource(nagiosplugin.Resource):

      def __init__(self, check, other_args):
         ...

Now you are able to inject contexts dynamically during probe execution. Note
that this is somewhat hacky. Separate resource discovery and metrics acquisition
if possible.


Stop Check.main() from calling `sys.exit`
-----------------------------------------

By default, `~nagiosplugin.check.Check.main` runs the check, prints its output
and exits the process. If you want to control process termination from the
outer scope, use `~nagiosplugin.check.Check.run` instead.

An invocation like this::

   def main():
      ...
      check.main(verbose, timeout)

can be replaced with the following code::

   def main():
      ...
      output, exitcode = check.run(verbose, timeout)
      sys.stdout.write(output)
      sys.exit(exitcode)


.. vim: set spell spelllang=en:
