# Hacking on/in source

## Setup

### Step 1 - Install bazel

As usual, Ubuntu's packaging of the Bazel bootstrap script is ... considerably stale.
Add the upstream Bazel ppa so we can get reasonably fresh builds.

``` sh
sudo apt install apt-transport-https curl gnupg
curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
sudo mv bazel.gpg /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
```

## Step 2 - Create a canonical `python`

Bazel, sadly, expects that a platform `python` exists for things.
Due to Bazel's plugins model, changing this is miserable.
On Archlinux, this isn't a problem. `python` is `python3`. But Ubuntu ... did the other thing.

``` sh
sudo apt install python-is-python3
```

### Step 3 - Non-hermetic build deps

The way that Bazel's Python toolchain(s) work is that ultimately they go out to the non-hermetic platform.
So, in order to be able to use the good tools we have to have some things on the host filesystem.

``` sh
if [[ "$(sqlite3 --version | awk -F'.' '/^3/ {print $2; exit}')" -lt 35 ]]; then
  echo "SQLite 3.35.0 or later  (select ... returning support) required"
  exit 1
fi

sudo apt install \
  python3-setuptools \
  postgresql libpq-dev \
  sqlite3 libsqlite3-dev
```

## Working in source

`source activate.sh` is the key.
It automates a number of tasks -
1. Building a virtualenv
2. Synchronizing the virtualenv from the requirements.txt
3. Updating the virtualenv with all project paths
4. Activating that virtualenv

`./tools/lint.sh` wraps up various linters into a one-stop shop.

`./tools/fmt.sh` wraps up various formatters into a one-stop shop.

`bazel build ...` will attempt to build everything.
While with a traditional build system this would be unreasonable, in Bazel which caches build products efficiently it's quite reasonable.

`bazel test ...` likewise will run (or know it doesn't need to run) all the tests.
