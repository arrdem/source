# Cram

> To force (people or things) into a place or container that is or appears to be too small to contain them.

An alternative to GNU Stow, which critically supports jinja2 templating and some other niceties.

## Usage

```
$ cram.zapp [hostname]
```


Cram consumes a directory tree of the following structure:

```
# Hosts
./hosts.d/<hostname>/
./hosts.d/<hostname>/REQUIRES
./hosts.d/<hostname>/PRE_INSTALL
./hosts.d/<hostname>/INSTALL
./hosts.d/<hostname>/POST_INSTALL

# Profiles
./profiles.d/<profilename>/
./profiles.d/<profilename>/REQUIRES
./profiles.d/<profilename>/PRE_INSTALL
./profiles.d/<profilename>/INSTALL
./profiles.d/<profilename>/POST_INSTALL

# Packages
./packages.d/<packagename>/
./packages.d/<packagename>/REQUIRES
./packages.d/<packagename>/PRE_INSTALL
./packages.d/<packagename>/POST_INSTALL
```
