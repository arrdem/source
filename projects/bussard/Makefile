.PHONY: deploy test

src/python/bussard/gen/parser.py: Makefile src/canopy/zonefile.peg
	mkdir -p tempdir
	cp src/canopy/zonefile.peg tempdir/
	canopy --lang=python tempdir/zonefile.peg
	which gsed && gsed -i 's/    /  /g' tempdir/zonefile.py || sed -i 's/    /  /g' tempdir/zonefile.py
	which gsed && gsed -i '1s/^/# checkstyle: noqa\n\n"""Generated code.\n\nDo not modify or lint\n"""\n\n/' tempdir/zonefile.py || sed -i '1s/^/# checkstyle: noqa\n\n"""Generated code.\n\nDo not modify or lint\n"""\n\n/' tempdir/zonefile.py
	mv tempdir/zonefile.py src/python/bussard/gen/parser.py

src/python/bussard/gen/types.py: Makefile src/canopy/zonefile.peg src/awk/gen_types.awk
	awk -f src/awk/gen_types.awk src/canopy/zonefile.peg > src/python/bussard/gen/types.py

all: src/python/bussard/gen/types.py src/python/bussard/gen/parser.py

test: all
	pytest
