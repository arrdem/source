# Reid's monorepo

I've found it inconvenient to develop lots of small Python modules.
And so I'm going the other way; Bazel in a monorepo with subprojects so I'm able to reuse a maximum of scaffolding.

## Projects

- [Datalog](projects/datalog) and the matching [shell](projects/datalog-shell)
- [YAML Schema](projects/yamlschema) (JSON schema with knowledge of PyYAML's syntax structure & nice errors)
- [Zapp! (now with a new home and releases)](https://github.com/arrdem/rules_zapp)
- [Flowmetal](projects/flowmetal)
- [Lilith](projects/lilith)

## Hacking (Ubuntu)

### Step 1 - Install bazel

As usual, Ubuntu's packaging of the Bazel bootstrap script is ... considerably stale.
Add the upstream Bazel ppa so we can get reasonably fresh builds.

``` sh
sudo apt install apt-transport-https curl gnupg
curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
sudo mv bazel.gpg /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
```

### Step 2 - Create a canonical `python`

Bazel, sadly, expects that a platform `python` exists for things.
Due to Bazel's plugins model, changing this is miserable.
So just create one.

``` sh
if ! `which python > /dev/null`; then
  sudo ln -s `which python3` /usr/bin/python
fi
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

### Working in source

`source activate.sh` is the key.
It automates a number of tasks -
1. Building a virtualenv
2. Synchronizing the virtualenv from the requirements.txt
3. Updating the virtualenv with all project paths
4. Activating that virtualenv

## License

Copyright Reid 'arrdem' McKenzie, 4/8/2021.

Unless labeled otherwise, the contents of this repository are distributed under the terms of the MIT license.
See the included `LICENSE` file for more.
