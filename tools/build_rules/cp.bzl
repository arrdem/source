load("@bazel_skylib//rules:copy_file.bzl",
     "copy_file",
)

def cp(name, src, **kwargs):
    """A slightly more convenient cp() rule. Name and out should always be the same."""

    rule_name = name.replace(".", "_").replace(":", "/").replace("//", "").replace("/", "_")
    copy_file(
        name = rule_name,
        src = src,
        out = name,
        **kwargs
    )
    return rule_name


def _copy_filegroup_impl(ctx):
    all_outputs = []
    for t in ctx.attr.deps:
        t_prefix = t.label.package
        for f in t.files.to_list():
            # Strip out the source prefix...
            path = f.short_path.replace(t_prefix + "/", "")
            out = ctx.actions.declare_file(path)
            print(ctx.attr.name, t.label, f, " => ", path)
            all_outputs += [out]
            ctx.actions.run_shell(
                outputs=[out],
                inputs=depset([f]),
                arguments=[f.path, out.path],
                command="cp $1 $2"
            )

    return [
        DefaultInfo(
            files=depset(all_outputs),
            runfiles=ctx.runfiles(files=all_outputs))
    ]


copy_filegroups = rule(
    implementation=_copy_filegroup_impl,
    attrs={
        "deps": attr.label_list(),
    },
)
