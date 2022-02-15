#!/usr/bin/env bash

set -ex

cd projects/cram

dest=$(mktemp -d)

./cram --help

# Should be able to list all packages
./cram list test/ | grep "packages.d/p1"

# P3 depends on P1, should show up in the listing
./cram list test/ packages.d/p3 | grep "packages.d/p1"

# P4 depends on P3, should show up in the listing
./cram list test/ packages.d/p4 | grep "packages.d/p3"

# The default profile should depend on its subpackage
./cram list test/ profiles.d/default | grep "profiles.d/default/subpackage"

# And the subpackage has a dep
./cram list test/ profiles.d/default/subpackage | grep "packages.d/p3"

# Install one package
./cram apply --no-optimize --require packages.d/p1 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
./cram state test/ | grep "${dest}/foo"
rm -r "${dest}"/*

# Install two transitively (legacy)
./cram apply --no-optimize --require packages.d/p3 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
./cram state test/ | grep "${dest}/foo"
./cram state test/ | grep "${dest}/bar"
rm -r "${dest}"/*

# Install two transitively (current)
./cram apply --no-optimize --require packages.d/p4 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
rm -r "${dest}"/*

# Install two transitively (current)
./cram apply --no-optimize --require packages.d/p4 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
rm -r "${dest}"/*

# Install two transitively (current)
./cram apply --no-optimize --require hosts.d/test --require profiles.d/default --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
rm -r "${dest}"/*

# INSTALL scripts get run as-is
./cram list test/ packages.d/p5 | grep "packages.d/p5/INSTALL"

# Inline scripts get pulled out repeatably
./cram list test/ packages.d/p6 | grep "b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b"

# Inline scripts get pulled out repeatably, even from the list format
./cram list test/ packages.d/p7 | grep "b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b"

# Test log-based optimization
./cram apply --no-optimize --require packages.d/p4 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
# These paths were already linked, they shouldn't be re-linked when optimizing.
! ./cram apply --require packages.d/p4 --optimize --execute test/ "${dest}" | grep "${dest}/foo"
! ./cram apply --require packages.d/p4 --optimize --execute test/ "${dest}" | grep "${dest}/bar"
rm -r "${dest}"/*

# Likewise, if we've exec'd this once we shouldn't do it again
./cram apply --no-optimize --require packages.d/p5 --execute test/ "${dest}"
! ./cram apply --require packages.d/p5 --execute test/ "${dest}" | grep "exec"

# ... unless the user tells us to
./cram apply --no-optimize --require packages.d/p5 --execute test/ "${dest}"
./cram apply --exec-always --require packages.d/p5 --execute test/ "${dest}" | grep "exec"

# If multiple packages provide the same _effective_ script, do it once
./cram apply --require packages.d/p6 --require packages.d/p7 --execute test/ "${dest}" | sort | uniq -c | grep "/tmp/stow/b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b.sh" | grep "1 - exec"

# Test log-based cleanup
./cram apply --require packages.d/p1 --require packages.d/p2 --execute test/ "${dest}"
[ -L "${dest}"/foo ]
[ -L "${dest}"/bar ]
# And how bar shouldn't be installed...
./cram state test/
./cram apply --require packages.d/p1 --execute test/ "${dest}"
./cram state test/
[ -L "${dest}"/foo ]
[ ! -L "${dest}"/bar ]
