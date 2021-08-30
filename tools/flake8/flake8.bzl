"""Linting for Python using Aspects."""


def _flake8_aspect_impl(target, ctx):
    if hasattr(ctx.rule.attr, 'srcs'):
        flake8 = ctx.attr._flake8.files_to_run
        config = ctx.attr._config.files.to_list()[0]

        files = []
        for src in ctx.rule.attr.srcs:
            for f in src.files.to_list():
                if f.extension == "py":
                    files.append(f)

        if files:
            report = ctx.actions.declare_file(ctx.label.name + ".report")
        else:
            return []

        args = ["--config", config.path, "--tee", "--output-file", report.path]
        for f in files:
            args.append(f.path)

        ctx.actions.run(
            executable = flake8,
            inputs = files,
            tools = ctx.attr._config.files.to_list() + ctx.attr._flake8.files.to_list(),
            arguments = args,
            outputs = [report],
            mnemonic = "Flake8",
        )

        return [
            OutputGroupInfo(flake8_checks = depset([report]))
        ]

    return []


flake8_aspect = aspect(
    implementation = _flake8_aspect_impl,
    attr_aspects = ['deps'],
    attrs = {
        '_flake8': attr.label(default="//tools/flake8"),
        '_config': attr.label(
            default="//:setup.cfg",
            executable=False,
            allow_single_file=True
        ),
    }
)


def _flake8_rule_impl(ctx):
    ready_targets = [dep for dep in ctx.attr.deps if "flake8_checks" in dir(dep[OutputGroupInfo])]
    files = depset([], transitive = [dep[OutputGroupInfo].flake8_checks for dep in ready_targets])
    return [DefaultInfo(files = files)]


flake8 = rule(
    implementation = _flake8_rule_impl,
    attrs = {
        'deps' : attr.label_list(aspects = [flake8_aspect]),
    },
)
