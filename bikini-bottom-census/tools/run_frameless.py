import sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
BASE, OUTDIR = sys.argv[1], sys.argv[2]
src = open(os.path.join(here, "thumb_variants.py")).read()
head, rest = src.split('if __name__ == "__main__":', 1)
tail = rest.split("# ---------- E: frameless floating flip tiles ----------", 1)[1]
ns = {"__file__": os.path.join(here, "thumb_variants.py"), "__name__": "tv"}
sys.argv = ["x", BASE, OUTDIR]
exec(compile(head + "\n" + tail, "thumb_variants.py", "exec"), ns)
for name, lab in (("E_flip_tiles", False), ("F_flip_tiles_label", True)):
    p = os.path.join(OUTDIR, f"thumbnail_{name}.jpg"); ns["compose"](ns["floating_flaps"](label=lab), p, top_y=4, lines=False); print(p, os.path.getsize(p))
