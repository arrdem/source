"""
Webp image building.
"""

def webp_image(src, name = None, out = None, quality = 95, flags = None):
     """Use cwebp to convert the image to an output."""

     out = out or src.split(".", 1)[0] + ".webp"
     name = name or out.replace(".", "_")
     return native.genrule(
         name = name,
         srcs = [src],
         outs = [out],
         cmd = "cwebp {} $< -o $@".format(
           " ".join([str(i) for i in (flags or ["-q", quality])])
         )
     )

def auto_webps(srcs):
    """Generate webp targets automagically for a mess of files."""

    for f in srcs:
        webp_image(
            src = f,
        )
