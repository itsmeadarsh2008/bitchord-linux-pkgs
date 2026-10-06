# BitChord for Linux — easy install + automatic updates

[BitChord](https://github.com/kushagrasinghx/BitChord) is a modern YouTube Music
client with Apple Music–inspired looks. Its desktop app for Linux is still in
**beta**, and the official project only posts manual downloads (a `.deb`, an
`.rpm`, an AppImage) — nothing that updates itself.

**This repo fixes that.** One command installs BitChord the *native* way for
your distro, and after that it updates together with everything else on your
system. No servers to maintain, no AUR account needed — a daily robot checks
for new BitChord releases and refreshes the install sources automatically.

> New to Linux? You only need the grey box in step 1. Everything else on this
> page is optional background reading.

---

## 1. Install in 30 seconds

Open a terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/itsmeadarsh2008/bitchord-linux-pkgs/main/install.sh | bash -s -- --yes
```

That's it. The script:

1. Figures out which Linux you use,
2. Adds a small BitChord software source (called a *repository*) for it,
3. Installs BitChord from that source,
4. Asks for your password once (normal — installing apps needs permission).

Want to see what it *would* do first without changing anything? Replace
`--yes` with `--check`:

```bash
curl -fsSL https://raw.githubusercontent.com/itsmeadarsh2008/bitchord-linux-pkgs/main/install.sh | bash -s -- --check
```

---

## 2. What happens on my distro?

| I use… | The script sets up… | From then on I update with… |
|---|---|---|
| Ubuntu, Debian, Mint, Pop!_OS | a BitChord APT source | `sudo apt upgrade` (or your Software app) |
| Fedora, RHEL, Rocky, AlmaLinux | a BitChord YUM repo | `sudo dnf upgrade` |
| openSUSE | a BitChord YUM repo | `sudo zypper dup` |
| Arch, CachyOS, EndeavourOS, Manjaro | a BitChord pacman repo, app name `bitchord-bin` | `paru -Syu`, or one click in **Cachy-Update** |
| Anything else | the official AppImage in `~/.local/bin` + a menu entry | re-run the command above |

### Prefer doing it by hand?

**Ubuntu / Debian / Mint:**
```bash
sudo tee /etc/apt/sources.list.d/bitchord.sources > /dev/null <<'EOF'
Types: deb
URIs: https://github.com/itsmeadarsh2008/bitchord-linux-pkgs/releases/download/current/
Suites: ./
Components:
Trusted: yes
EOF
sudo apt-get update
sudo apt-get install bitchord
```

**Fedora / RHEL / openSUSE:**
```bash
sudo tee /etc/yum.repos.d/bitchord.repo > /dev/null <<'EOF'
[bitchord]
name=BitChord (bitchord-linux-pkgs)
baseurl=https://itsmeadarsh2008.github.io/bitchord-linux-pkgs/yum
enabled=1
gpgcheck=0
repo_gpgcheck=0
EOF
# Fedora / RHEL:
sudo dnf install bitchord
# openSUSE instead:
sudo zypper install bitchord
```

**Arch / CachyOS** — add to the bottom of `/etc/pacman.conf`:
```ini
[bitchord]
SigLevel = Optional TrustAll
Server = https://github.com/itsmeadarsh2008/bitchord-linux-pkgs/releases/download/current
```
then:
```bash
paru -Sy bitchord-bin
```

---

## 3. Uninstall

Changed your mind? Remove the app and (optionally) the software source:

```bash
# Ubuntu / Debian
sudo apt-get remove bitchord
sudo rm /etc/apt/sources.list.d/bitchord.sources

# Fedora / RHEL
sudo dnf remove bitchord
sudo rm /etc/yum.repos.d/bitchord.repo

# openSUSE
sudo zypper remove bitchord
sudo rm /etc/yum.repos.d/bitchord.repo

# Arch / CachyOS
paru -R bitchord-bin
# then delete the [bitchord] block from /etc/pacman.conf
```

---

## 4. Questions beginners ask

**Is this the official BitChord app?**
The music app itself is 100% the official build by
[kushagrasinghx](https://github.com/kushagrasinghx/BitChord) — this repo just
re-packages the download so your system can update it. Nothing is modified.

**Is it safe?**
The install sources are unsigned (`Trusted: yes` / `Optional TrustAll`), which
means your system trusts this repo without a signature check. That is normal
for small community repos, but understand what it means: only use it if you
trust this GitHub account. The packages themselves come straight from the
official BitChord releases.

**Why does it ask for my password?**
Adding a software source and installing apps affects the whole computer, so
Linux asks you to confirm. The script never sends your password anywhere.

**Which version do I get?**
Always the latest stable BitChord release. A robot in this repo checks every
day and publishes new packages within ~24 hours of upstream.

**The desktop app says beta — what does that mean?**
Expect rough edges (the packager adds a menu icon and terminal command because
upstream's Linux packages don't include one yet). Your music, playlists and
logins live in your BitChord account, so updates won't wipe them — but beta
means keep a backup of anything precious.

**`curl: command not found`?**
Install it first: `sudo apt install curl` (Ubuntu/Debian),
`sudo dnf install curl` (Fedora), or `sudo pacman -S curl` (Arch) — then
re-run step 1.

---

## 5. Troubleshooting

- **Download is slow or fails (404):** a new BitChord release may have renamed
  its files, or GitHub is having a bad day. Wait an hour, re-run. If it
  persists, open an issue here with the full error text.
- **Ubuntu warns the repo is "not signed":** expected — this repo is
  intentionally unsigned (see safety note above). As long as the line says
  `Trusted: yes`, `apt-get update` will proceed.
- **Fedora says "no package bitchord available":** the repo metadata may still
  be building (check the Actions tab above). Wait a few minutes and try again.
- **Arch: `paru -Syu` doesn't offer an update:** run `paru -Sy` once to refresh
  databases, or check that the `[bitchord]` block is still in
  `/etc/pacman.conf`.
- **AppImage won't start:** make sure it's executable —
  `chmod +x ~/.local/bin/BitChord.AppImage` — and that you're on 64-bit
  Intel/AMD Linux.

---

## 6. For advanced users

Daily GitHub Action (`.github/workflows/repo.yml`):

1. Reads the latest upstream tag from the BitChord releases API.
2. Bumps `PKGBUILD` if needed and rebuilds the Arch package (`makepkg`,
   repack of the official `.deb` — no compiling, `!debug`).
3. Generates all three repo formats from the official binaries:
   `repo-add` → pacman `bitchord.db*`, `tools/mkapt.py` → APT
   `Packages`/`Release` (flat repo), `createrepo_c --location-prefix …`
   → YUM `repodata` with absolute RPM URLs.
4. Publishes binaries + metadata to the floating `current` Release
   (~300 MB each — too big for git/Pages, fine for Releases) and deploys
   only the tiny YUM `repodata` to GitHub Pages.

Repo files consumed by `install.sh`: `bitchord.sources` (APT),
`bitchord.repo` (YUM). Upstream asset names have drifted before
(`1.8` vs `1.8-beta1`), so if a run 404s, check the upstream Releases page
and adjust the name patterns in the workflow.

License of BitChord itself: GPL-3.0 (see upstream).
