"""A tiny template(s) tool.

Processes Jekyll/Hyde/Hugo/... style 'fontmatter' headers, applying Jinja2/Liquid templating from an
optional templates and includes directory.

"""

import os
import re

import click
import jinja2
import yaml

FONTMATTER_PATTERN = re.compile(
    r"^(---\n\r?(?P<fontmatter>.*?)\n\r?---\n\r?)?(?P<content>.+)$", re.DOTALL
)


@click.command()
@click.option("-i", "--include", "include_dir", multiple=True)
@click.option("-t", "--template", "template_dir", multiple=True)
@click.option("-c", "--config", "config_file")
@click.argument("infile")
@click.argument("outfile")
def main(include_dir, template_dir, config_file, infile, outfile):
    """Apply templating.

    Consume infile, processing it with templating and write the results to outfile.

    """

    loaders = []
    for d in include_dir:
        loaders.append(jinja2.FileSystemLoader(os.path.realpath(d)))

    for d in template_dir:
        loaders.append(jinja2.FileSystemLoader(os.path.realpath(d)))

    # Build a j2 environment using the potentially various loaders..
    environment = jinja2.Environment(loader=jinja2.ChoiceLoader(loaders))

    # Load a site config
    if config_file:
        with open(config_file) as f:
            site = yaml.safe_load(f.read())
    else:
        site = {}

    # Figure out doing the fontmatter nonsense...
    with open(infile, "r") as f:
        buff = f.read()

    match = re.match(FONTMATTER_PATTERN, buff)
    if fontmatter := match.group("fontmatter"):
        fontmatter = yaml.safe_load(fontmatter)
    else:
        fontmatter = {}

    # Render the file contents
    template = environment.from_string(match.group("content"))
    content = template.render(site=site, page=fontmatter)

    # If there's a configured `layout:` stick the content in the layout.
    if "layout" in fontmatter:
        template = environment.get_template(fontmatter.get("layout"))
        content = template.render(content=content, site=site, page=fontmatter)

    # And dump the results
    with open(outfile, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
