"""Repack an unpacked PPTX directory into a .pptx (no `zip` binary on Windows)."""
import os, sys, zipfile

def pack(src_dir, out):
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml must be the first entry in an OOXML package.
        ct = os.path.join(src_dir, "[Content_Types].xml")
        if os.path.exists(ct):
            z.write(ct, "[Content_Types].xml")
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src_dir).replace(os.sep, "/")
                if rel == "[Content_Types].xml":
                    continue
                z.write(full, rel)
    return out

if __name__ == "__main__":
    print("wrote", pack(sys.argv[1], sys.argv[2]))
