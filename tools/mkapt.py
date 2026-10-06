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
import tarfile
import io


def run(*args):
    return subprocess.run(args, check=True, capture_output=True)


def bsdtar_list(deb):
    p = run("bsdtar", "-tf", deb)
    return p.stdout.decode().splitlines()


def bsdtar_extract(deb, member):
    p = run("bsdtar", "-O", "-xf", deb, member)
    return p.stdout


def get_control(deb_path):
    members = bsdtar_list(deb_path)
    ctrl = next((m for m in members if m.startswith("control.tar")), None)
    if ctrl is None:
        raise ValueError(f"{deb_path}: no control.tar.* member")
    data = bsdtar_extract(deb_path, ctrl)
    if data[:2] == b"\x1f\x8b":
        mode = "r:gz"
    elif data[:3] == b"BZh":
        mode = "r:bz2"
    elif data[:6] == b"\xfd7zXZ\x00":
        mode = "r:xz"
    else:
        mode = "r:"
    with tarfile.open(fileobj=io.BytesIO(data), mode=mode) as tf:
        for m in tf.getmembers():
            if m.name in ("control", "./control"):
                f = tf.extractfile(m)
                return f.read().decode("utf-8", "replace")
    raise ValueError(f"{deb_path}: no control file inside {ctrl}")


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
