#!/usr/bin/env python3
"""Generate flat APT repository metadata (Packages, Packages.gz, Release)
for .deb files in a directory. Requires bsdtar (libarchive).

Usage: mkapt.py <deb-dir> <out-dir>
  Reads *.deb in <deb-dir>, writes Packages/Packages.gz/Release to <out-dir>.
  Filenames in Packages are basenames (flat repo, same dir as metadata).
"""

import argparse
import gzip
import hashlib
import os
import shutil
import subprocess
import sys


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def bsdtar_list(deb):
    p = run("bsdtar", "-tf", deb)
    return p.stdout.decode().splitlines()


def get_control(deb_path):
    """Extract debian/control text using bsdtar only (handles any
    control.tar compression incl. zstd, which python-tarfile can't)."""
    members = bsdtar_list(deb_path)
    ctrl = next((m for m in members if m.startswith("control.tar")), None)
    if ctrl is None:
        raise ValueError(f"{deb_path}: no control.tar.* member")
    p1 = subprocess.Popen(
        ["bsdtar", "-O", "-xf", deb_path, ctrl], stdout=subprocess.PIPE
    )
    try:
        # bsdtar reads the (possibly compressed) tar from stdin
        p2 = subprocess.run(
            ["bsdtar", "-x", "-O", "-f", "-", "control"],
            stdin=p1.stdout,
            capture_output=True,
        )
        if p2.returncode != 0 or not p2.stdout:
            # retry with ./control variant
            p1.terminate()
            p1 = subprocess.Popen(
                ["bsdtar", "-O", "-xf", deb_path, ctrl], stdout=subprocess.PIPE
            )
            p2 = subprocess.run(
                ["bsdtar", "-x", "-O", "-f", "-", "./control"],
                stdin=p1.stdout,
                capture_output=True,
            )
        if p2.returncode != 0 or not p2.stdout:
            raise ValueError(f"control extract failed: {p2.stderr.decode()[:200]}")
        return p2.stdout.decode("utf-8", "replace")
    finally:
        try:
            p1.stdout.close()
        except Exception:
            pass
        p1.wait()


def parse_control(text):
    fields = {}
    cur = None
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and cur:
            fields[cur] += "\n" + line
        elif ":" in line:
            k, v = line.split(":", 1)
            cur = k.strip()
            fields[cur] = v.strip()
    return fields


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deb_dir")
    ap.add_argument("out_dir")
    args = ap.parse_args()

    debs = sorted(f for f in os.listdir(args.deb_dir) if f.endswith(".deb"))
    if not debs:
        print("mkapt: no .deb files found", file=sys.stderr)
        sys.exit(1)
    os.makedirs(args.out_dir, exist_ok=True)

    entries = []
    for fn in debs:
        p = os.path.join(args.deb_dir, fn)
        fields = parse_control(get_control(p))
        size = os.path.getsize(p)
        entry = [
            f"Package: {fields.get('Package', 'unknown')}",
            f"Version: {fields.get('Version', '0')}",
            f"Architecture: {fields.get('Architecture', 'amd64')}",
        ]
        for k in (
            "Maintainer",
            "Depends",
            "Pre-Depends",
            "Description",
            "Section",
            "Priority",
            "Homepage",
            "Installed-Size",
        ):
            if k in fields:
                entry.append(f"{k}: {fields[k]}")
        entry += [
            f"Filename: {fn}",
            f"Size: {size}",
            f"SHA256: {sha256_of(p)}",
        ]
        entries.append("\n".join(entry) + "\n")
    packages = "\n".join(entries)
    with open(os.path.join(args.out_dir, "Packages"), "w") as f:
        f.write(packages)
    with open(os.path.join(args.out_dir, "Packages"), "rb") as fin:
        with gzip.open(os.path.join(args.out_dir, "Packages.gz"), "wb") as fout:
            shutil.copyfileobj(fin, fout)

    import datetime

    rel = [
        "Origin: bitchord-linux-pkgs",
        "Label: bitchord",
        f"Date: {datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S UTC')}",
        "Architectures: amd64",
        "Components: ",
        "Description: BitChord flat repo",
    ]
    for fn in ("Packages", "Packages.gz"):
        p = os.path.join(args.out_dir, fn)
        rel.append(f"SHA256:\n {sha256_of(p)} {os.path.getsize(p)} {fn}")
    with open(os.path.join(args.out_dir, "Release"), "w") as f:
        f.write("\n".join(rel) + "\n")
    print(f"mkapt: wrote {len(debs)} package(s) -> {args.out_dir}/")


if __name__ == "__main__":
    main()
