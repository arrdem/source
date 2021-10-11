# Cram

> To force (people or things) into a place or container that is or appears to be too small to contain them.

An alternative to GNU Stow, more some notion of packages with dependencies and install scripts.

## Usage

```
# cram [--dry-run | --execute] <configdir> <destdir>
$ cram ~/conf ~/  # --dry-run is the default
```

Cram operates in terms of packages, which are directories with the following structure -

```
/REQUIRES      # A list of other packages this one requires
/BUILD         # 1. Perform any compile or package management tasks
/PRE_INSTALL   # 2. Any other tasks required before installation occurs
/INSTALL       # 3. Do whatever constitutes installation
/POST_INSTALL  # 4. Any cleanup or other tasks following installation

...            # Any other files are treated as package contents

```

Cram reads a config dir with three groups of packages
- `packages.d/<packagename>` contains a package that installs but probably shouldn't configure a given tool, package or group of files.
  Configuration should be left to profiles.
- `profiles.d/<profilename>` contains a profile; a group of related profiles and packages that should be installed together.
- `hosts.d/<hostname>` contains one package for each host, and should pull in a list of profiles.

The intent of this tool is to keep GNU Stow's intuitive model of deploying configs via symlinks, and augment it with a useful pattern for talking about "layers" / "packages" of related configs.

Cram installs the package `hosts.d/$(hostname)`, and `profiles.d/default` by default.
