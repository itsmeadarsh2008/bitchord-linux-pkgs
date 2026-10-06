# bitchord-linux-pkgs

Universal Linux installer + serverless pacman repo for [BitChord](https://github.com/kushagrasinghx/BitChord).
No VPS — GitHub Actions builds, GitHub Releases hosts the binary repo. Chaotic-AUR style, minimal.

## Universal install (any distro)

```bash
curl -fsSL https://raw.githubusercontent.com/itsmeadarsh2008/bitchord-linux-pkgs/main/install.sh | bash -s -- --yes
```

Preview first: replace `--yes` with `--check`. Pin a version: add `--version 1.8`.

| Distro | What it does | Updates via |
|---|---|---|
| Arch / CachyOS / EndeavourOS / Manjaro | adds `[bitchord]` pacman repo, installs `bitchord-bin` | `paru -Syu` / Cachy-Update one-click |
| Debian / Ubuntu / Mint / Pop!_OS | adds `bitchord.sources` flat APT repo, installs from it | `apt upgrade` |
| Fedora / RHEL / Rocky / Alma | adds `bitchord.repo` YUM repo, installs from it | `dnf upgrade` |
| openSUSE | adds `bitchord.repo` YUM repo, installs from it | `zypper dup` |
| Anything else | upstream `.AppImage` → `~/.local/bin` + desktop entry | re-run script |

## Arch details (one-click in Cachy-Update afterwards)

One-liner (adds repo if missing, syncs):

```bash
grep -q "^\[bitchord\]" /etc/pacman.conf || printf '\n[bitchord]\nSigLevel = Optional TrustAll\nServer = https://github.com/itsmeadarsh2008/bitchord-linux-pkgs/releases/download/current\n' | sudo tee -a /etc/pacman.conf >/dev/null && paru -Sy
```

Or manually, add to `/etc/pacman.conf`:

```ini
[bitchord]
SigLevel = Optional TrustAll
Server = https://github.com/itsmeadarsh2008/bitchord-linux-pkgs/releases/download/current
```

Install / update with `paru`:

```bash
paru -Sy bitchord-bin
paru -Syu # regular updates, also picked up by Cachy-Update
```

After that, Cachy-Update (`checkupdates` + `paru -Syu`) lists updates automatically.
Click Update = updated.

## How it updates

`.github/workflows/repo.yml` runs daily + on demand:

1. Checks `api.github.com/repos/kushagrasinghx/BitChord/releases/latest`
2. If tag != `pkgver` in `PKGBUILD`, bumps `pkgver`, resets `pkgrel=1`, runs `updpkgsums`
3. Regenerates `.SRCINFO`, builds Arch package with `makepkg --nodeps` (repack of official `.deb`, no compile, `!debug`)
4. `repo-add` → `bitchord.db*`; `tools/mkapt.py` → APT `Packages`/`Release`; `createrepo_c --location-prefix <current-release-URL>` → YUM `repodata`
5. Uploads everything to floating `current` Release (binaries ~300MB each — over git/Pages 100MB limit, under Releases 2GB limit); deploys only tiny YUM `repodata` to Pages

Trigger manually: Actions tab → `repo` → Run workflow.

## Repo files (consumed by `install.sh`)

- `bitchord.sources` — deb822 APT source, `Suites: ./`, `Trusted: yes` (flat repo on the `current` Release)
- `bitchord.repo` — YUM repo, `baseurl` = Pages-hosted `repodata`, RPMs via absolute URLs

## Files

- `PKGBUILD` — repacks official `BitChord-<ver>-linux-amd64.deb`
- `.SRCINFO` — generated, keep in sync (`makepkg --printsrcinfo > .SRCINFO`)
- `.github/workflows/repo.yml` — bump + build + Pages deploy

## Notes

- Upstream Linux naming has been `BitChord-<ver>-linux-amd64.deb` vs Windows `1.8-beta1`. If a future release 404s, check the Releases page and adjust `source=()` accordingly.
- `SigLevel = Optional TrustAll` = unsigned repo, fine for personal use. For public use, sign with GPG and switch to `Required`.
- License of BitChord itself: GPL-3.0 (see upstream).
