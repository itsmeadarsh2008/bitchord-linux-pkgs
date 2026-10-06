# bitchord-linux-pkgs

Serverless pacman repo for [BitChord](https://github.com/kushagrasinghx/BitChord) on Arch / CachyOS.
No VPS — GitHub Actions builds, GitHub Releases hosts the binary repo. Chaotic-AUR style, minimal.

## Use it (one-click in Cachy-Update afterwards)

Add to `/etc/pacman.conf`:

```ini
[bitchord]
SigLevel = Optional TrustAll
Server = https://github.com/itsmeadarsh2008/bitchord-linux-pkgs/releases/download/current
```

Then:

```bash
sudo pacman -Sy
sudo pacman -S bitchord-bin
```

After that, Cachy-Update (`checkupdates` + `pacman -Syu`) lists updates automatically.
Click Update = updated. No AUR helper needed for this package.

## How it updates

`.github/workflows/repo.yml` runs daily + on demand:

1. Checks `api.github.com/repos/kushagrasinghx/BitChord/releases/latest`
2. If tag != `pkgver` in `PKGBUILD`, bumps `pkgver`, resets `pkgrel=1`, runs `updpkgsums`
3. Regenerates `.SRCINFO`, builds with `makepkg --nodeps` (repack of official `.deb`, no compile, `!debug`)
4. `repo-add` into `bitchord.db.tar.zst`
5. Uploads `*.pkg.tar.zst + bitchord.db*` to floating `current` Release (keeps only latest — each build is ~300MB, over git/Pages 100MB limit, under Releases 2GB limit)

Trigger manually: Actions tab → `repo` → Run workflow.

## Files

- `PKGBUILD` — repacks official `BitChord-<ver>-linux-amd64.deb`
- `.SRCINFO` — generated, keep in sync (`makepkg --printsrcinfo > .SRCINFO`)
- `.github/workflows/repo.yml` — bump + build + Pages deploy

## Notes

- Upstream Linux naming has been `BitChord-<ver>-linux-amd64.deb` vs Windows `1.8-beta1`. If a future release 404s, check the Releases page and adjust `source=()` accordingly.
- `SigLevel = Optional TrustAll` = unsigned repo, fine for personal use. For public use, sign with GPG and switch to `Required`.
- License of BitChord itself: GPL-3.0 (see upstream).
