"""
The Calf package infrastructure.

Calf's packaging infrastructure is very heavily inspired by Maven, and seeks first and foremost to
provide statically understandable, repeatable builds.

However the loading infrastructure is designed to simultaneously support from-source builds
appropriate to interactive development workflows and monorepos.
"""

from collections import namedtuple


class CalfLoaderConfig(namedtuple("CalfLoaderConfig", ["paths"])):
    """
  """


class CalfDelayedPackage(
    namedtuple("CalfDelayedPackage", ["name", "version", "metadata", "path"])
):
    """
  This structure represents the delay of loading a packaage.

  Rather than eagerly analyze packages, it may be profitable to use lazy loading / lazy resolution
  of symbols. It may also be possible to cache analyzing some packages.
  """


class CalfPackage(
    namedtuple("CalfPackage", ["name", "version", "metadata", "modules"])
):
    """
  This structure represents the result of forcing the load of a package, and is the product of
  either loading a package directly, or a package becoming a direct dependency and being forced.
  """


def parse_package_requirement(config, env, requirement):
    """
  :param config:
  :param env:
  :param requirement:
  :returns:

  
  """


def analyze_package(config, env, package):
    """
  :param config:
  :param env:
  :param module:
  :returns:

  Given a loader configuration and an environment to load into, analyzes the requested package,
  returning an updated environment.
  """
