"""Linting for Python using Aspects."""

# Hacked up from https://github.com/bazelbuild/rules_rust/blob/main/rust/private/clippy.bzl
#
# Usage:
#   bazel build --aspects="//tools/flake8:flake8.bzl%flake8_aspect" --output_groups=flake8_checks <target|pattern>
#
# Note that the build directive can be inserted to .bazelrc to make it part of the default behavior

def _black_aspect_impl(target, ctx):
    if hasattr(ctx.rule.attr, 'srcs'):
        black = ctx.attr._black.files_to_run
        config = ctx.attr._config.files.to_list()[0]

        files = []
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if f.extension == "py":
                    files.append(f)

        if files:
            report = ctx.actions.declare_file(ctx.label.name + ".black.report")
        else:
            return []

        args = ["--check", "--output-file", report.path]
        for f in files:
            args.append(f.path)

        ctx.actions.run(
            executable = black,
            inputs = files,
            tools = ctx.attr._config.files.to_list() + ctx.attr._black.files.to_list(),
            arguments = args,
            outputs = [report],
            mnemonic = "Black",
        )

        return [
            OutputGroupInfo(black_checks = depset([report]))
        ]

    return []


black_aspect = aspect(
    implementation = _black_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        '_black': attr.label(default=":black"),
        '_config': attr.label(
            default="//:setup.cfg",
            executable=False,
            allow_single_file=True
        ),
    }
)


def _black_rule_impl(ctx):
    ready_targets = [dep for dep in ctx.attr.deps if "black_checks" in dir(dep[OutputGroupInfo])]
    files = depset([], transitive = [dep[OutputGroupInfo].black_checks for dep in ready_targets])
    return [DefaultInfo(files = files)]


black = rule(
    implementation = _black_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [black_aspect]),
    },
)
