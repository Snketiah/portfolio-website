#!/usr/bin/env python3
"""Prepare images and videos for the site.

Images go through macOS `sips`; videos through ffmpeg (H.264, no audio unless --audio).

  python3 tools/media.py img  SRC DEST [--max 1800] [--crop W H [X Y]] [--quality 78]
  python3 tools/media.py vid  SRC DEST [--max 1280] [--audio] [--crf 26] [--trim START END] [--crop W:H:X:Y]
  python3 tools/media.py poster SRC.mp4 DEST.jpg [--at 1.0]

DEST extension decides the image format: .jpg for photos, .png for screenshots/diagrams.
--crop for images is a centred crop (sips -c) unless X Y are given (then ffmpeg crops exactly).
All paths are relative to the current directory. Run from the `site/` folder.
"""
import argparse, os, shutil, subprocess, sys, tempfile


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def img(a):
    os.makedirs(os.path.dirname(a.dest) or ".", exist_ok=True)
    fmt = "png" if a.dest.lower().endswith(".png") else "jpeg"
    with tempfile.TemporaryDirectory() as t:
        src = a.src
        if a.crop and len(a.crop) == 4:
            w, h, x, y = a.crop
            tmp = os.path.join(t, "crop.png")
            run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"crop={w}:{h}:{x}:{y}", tmp])
            src = tmp
        tmp2 = os.path.join(t, "out." + ("png" if fmt == "png" else "jpg"))
        cmd = ["sips", "-s", "format", fmt]
        if fmt == "jpeg":
            cmd += ["-s", "formatOptions", str(a.quality)]
        if a.crop and len(a.crop) == 2:
            cmd += ["-c", str(a.crop[1]), str(a.crop[0])]  # sips -c takes H W
        cmd += [src, "--out", tmp2]
        if not os.path.exists(src):
            sys.exit(f"source not found: {src}")
        run(cmd)
        if not os.path.exists(tmp2):
            sys.exit(f"sips could not convert {src}")
        # sips -Z re-saves at its default quality, so resize first, then re-encode at the chosen quality
        run(["sips", "-Z", str(a.max), tmp2])
        if fmt == "jpeg":
            tmp3 = os.path.join(t, "final.jpg")
            run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(a.quality), tmp2, "--out", tmp3])
            tmp2 = tmp3
        shutil.move(tmp2, a.dest)
    print(a.dest, os.path.getsize(a.dest) // 1024, "KB")


def vid(a):
    os.makedirs(os.path.dirname(a.dest) or ".", exist_ok=True)
    vf = []
    if a.crop:
        vf.append(f"crop={a.crop}")
    vf.append(f"scale='if(gt(iw,ih),min({a.max},iw),-2)':'if(gt(iw,ih),-2,min({a.max},ih))'")
    vf.append("format=yuv420p")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if a.trim:
        cmd += ["-ss", str(a.trim[0]), "-to", str(a.trim[1])]
    cmd += ["-i", a.src, "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "slow",
            "-crf", str(a.crf), "-movflags", "+faststart", "-r", "30"]
    cmd += ["-c:a", "aac", "-b:a", "128k"] if a.audio else ["-an"]
    run(cmd + [a.dest])
    print(a.dest, os.path.getsize(a.dest) // 1024, "KB")


def poster(a):
    os.makedirs(os.path.dirname(a.dest) or ".", exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(a.at), "-i", a.src, "-frames:v", "1", "-q:v", "4", a.dest])
    print(a.dest, os.path.getsize(a.dest) // 1024, "KB")


p = argparse.ArgumentParser()
sp = p.add_subparsers(dest="cmd", required=True)
i = sp.add_parser("img"); i.add_argument("src"); i.add_argument("dest")
i.add_argument("--max", type=int, default=1800); i.add_argument("--quality", type=int, default=78)
i.add_argument("--crop", type=int, nargs="+")
v = sp.add_parser("vid"); v.add_argument("src"); v.add_argument("dest")
v.add_argument("--max", type=int, default=1280); v.add_argument("--crf", type=int, default=26)
v.add_argument("--audio", action="store_true"); v.add_argument("--trim", type=float, nargs=2)
v.add_argument("--crop")
po = sp.add_parser("poster"); po.add_argument("src"); po.add_argument("dest"); po.add_argument("--at", type=float, default=1.0)
a = p.parse_args()
{"img": img, "vid": vid, "poster": poster}[a.cmd](a)
