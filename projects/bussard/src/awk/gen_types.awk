BEGIN {
    print "#!/usr/bin/env python3\n"
    print "\"\"\"GENERATED.\n\nRecord types derived from the grammar.\n\"\"\"\n";
    print "from typing import NamedTuple, Optional\n\n";
		print "class Record(object):\n  \"\"\"Base class for DNS records.\"\"\"\n\n"
    spacing=""
}

/<-/ {
    if (or(("\""$1"\"" == tolower($3)), ("\"$"$1"\"" == tolower($3)))) {
        if (spacing)
            print spacing;

        print "class " toupper($1) "(NamedTuple, Record):  # noqa: T000";

        # If this isn't $TTL or $ORIGIN, it has a name.
        if ($3 !~ /\$/)
            print "  name: str";

        for(i=3;i<=NF;i++) {
            if ($i ~ /:/) {
                split($i,arr,":")

                if ($i ~ /:(word|v[46]address|string)/) {
                    print "  " arr[1] ": str";
                } else if ($i ~ /:(num|seconds)/) {
                    print "  " arr[1] ": int"
                }
            }
        }
        print "  type: str = \"IN\"";
        print "  ttl: Optional[int] = None";
        print "  comment: Optional[str] = None";
        spacing="\n";
    }
}
