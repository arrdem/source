#!/usr/bin/env python3

"""A documentation generator.

This is a shim tool which wraps up a whole bunch of Sphinx internals in a single "convenient"
entrypoint. Former tweeps may recognize some parallels to the `docbird` tool developed by Twitter's
techdocs team.

"""

import builtins
from functools import wraps
import io
import os
import sys

import click
import livereload
from sphinx.application import Sphinx
from sphinx.cmd.quickstart import main as new
from sphinx.ext.apidoc import main as apidoc
from sphinx.ext.autosummary.generate import main as autosummary
from sphinx.util.docutils import docutils_namespace, patch_docutils


@click.group()
def cli():
    """A documentation generator.

    Just a shim to a variety of upstream Sphinx commands typically distributed as separate binaries
    for some dang reason.

    Note that due to subcommand argument parsing '-- --help' is likely required.

    Subcommands have not been renamed (or customized, yet) from their Sphinx equivalents.

    """


@cli.group()
def generate():
    """Subcommands for doing RST header generation."""


@generate.command(
    "apidoc",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def do_apidoc(argv):
    """Use sphinx.ext.apidoc to generate API documentation."""
    return apidoc(argv)


@generate.command(
    "summary",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def do_summary(argv):
    """Use sphinx.ext.autosummary to generate module summaries."""
    return autosummary(argv)


@cli.command(
    "new",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("argv", nargs=-1, type=click.UNPROCESSED)
def do_new(argv):
    """Create a new Sphinx in the current directory."""
    return new(argv)


@cli.command(
    "build",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("sourcedir")
@click.argument("outputdir")
@click.option("-c", "--confdir")
@click.option("-d", "--doctreedir")
@click.option("-b", "--builder", default="html")
@click.option("--freshenv/--no-freshenv", default=False)
@click.option("-W", "--warning-is-error", "werror", is_flag=True, flag_value=True)
@click.option("-t", "--tag", "tags", multiple=True)
def do_build(
    sourcedir, outputdir, confdir, doctreedir, builder, freshenv, werror, tags
):
    """Build a single Sphinx project."""

    if not confdir:
        confdir = sourcedir

    if not doctreedir:
        doctreedir = os.path.join(outputdir, ".doctrees")

    status = sys.stdout
    warning = sys.stderr
    # error = sys.stderr

    confdir = confdir or sourcedir
    confoverrides = {}  # FIXME: support these
    with patch_docutils(confdir), docutils_namespace():
        app = Sphinx(
            sourcedir,
            confdir,
            outputdir,
            doctreedir,
            builder,
            confoverrides,
            status,
            warning,
            freshenv,
            werror,
            tags,
            1,
            4,
            False,
        )
        app.build(True, [])
        return app.statuscode


@cli.command(
    "serve",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.option("-h", "--host", default="localhost")
@click.option("-p", "--port", type=int, default=8080)
@click.argument("sourcedir")
@click.argument("outputdir")
def do_serve(host, port, sourcedir, outputdir):
    """Build and then serve a Sphinx tree."""

    sourcedir = os.path.realpath(sourcedir)
    outputdir = os.path.realpath(outputdir)

    server = livereload.Server()

    # HACK (arrdem 2020-10-31):
    #   Okay. This is an elder hack, and I'm proud of it.
    #
    #   The naive implementation of the watching server is to watch the input files, which is
    #   obviously correct. However, Sphinx has a BUNCH of operators like include and mdinclude and
    #   soforth which can cause a Sphinx doctree to have file dependencies OUTSIDE of the "trivial"
    #   source path dependency set.
    #
    #   In order to make sure that rebuilding does what the user intends, we trace calls to the
    #   open() function and attempt to dynamically discover the dependency set of the site. This
    #   allows us to trigger strictly correct rebuilds unlike other Sphinx implementations which
    #   need to be restarted under some circumstances.
    def opener(old_open):
        @wraps(old_open)
        def tracking_open(path, mode="r", *args, **kw):
            file = old_open(path, mode, *args, **kw)
            if isinstance(path, int):
                # If you're doing something weird with file pointers, ignore it.
                pass
            else:
                path = os.path.realpath(path)

                if "w" in mode:
                    # If we're writing a file, it's an output for sure. Ignore it.
                    ignorelist.add(path)
                elif (
                    not path.startswith(outputdir)
                    and path not in ignorelist
                    and path not in watchlist
                ):
                    # Watch any source file (file we open for reading)
                    server.watch(path, build)
                    watchlist.add(path)
            return file

        return tracking_open

    ignorelist = set()
    watchlist = set()

    def build():
        try:
            old_open = open
            builtins.open = opener(old_open)
            io.open = opener(old_open)
            do_build([sourcedir, outputdir])
        except SystemExit:
            pass
        finally:
            builtins.open = old_open
            io.open = old_open

    build()
    server.watch(
        "conf.py", build
    )  # Not sure why this isn't picked up, but it doesn't seem to be.

    server.serve(port=port, host=host, root=outputdir)


if __name__ == "__main__":
    # Hack in a -- delimeter to bypass click arg parsing
    if not (sys.argv + [""])[1].startswith("-"):
        sys.argv = [sys.argv[0], "--"] + sys.argv[1:]

    # Use click subcommands for everything else
    exit(cli())
