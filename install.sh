#!/usr/bin/env bash
# Universal BitChord installer for Linux — repo-based everywhere, so every
# distro family gets real auto-updates (apt upgrade / dnf upgrade / paru -Syu).
# Arch/CachyOS -> pacman repo | Debian/Ubuntu -> flat APT repo
# Fedora/RHEL/openSUSE -> YUM repo | everything else -> upstream AppImage
set -euo pipefail

UPSTREAM_REPO="kushagrasinghx/BitChord"
PKG_REPO="itsmeadarsh2008/bitchord-linux-pkgs"
REPO_ID="bitchord"
REPO_SERVER="https://github.com/${PKG_REPO}/releases/download/current"
REPO_RAW="https://raw.githubusercontent.com/${PKG_REPO}/main"
YUM_BASEURL="https://itsmeadarsh2008.github.io/bitchord-linux-pkgs/yum"
PKG="bitchord-bin"
APPIMAGE_NAME="BitChord.AppImage"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--check] [--yes] [--version X.Y]

  --check      print detected distro + URLs, change nothing
  --yes        non-interactive (passes -y/--noconfirm where supported)
  --version    install a specific upstream version (default: latest release)
EOF
}

CHECK=0; ASSUME_YES=0; WANT_VER=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK=1; shift ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    --version) WANT_VER="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 1; }; }
need curl; need python3

# --- resolve version + asset URLs from upstream GitHub API ---
API_JSON=$(curl -fsSL "https://api.github.com/repos/${UPSTREAM_REPO}/releases/${WANT_VER:+tags/v}${WANT_VER:-latest}")
eval "$(echo "$API_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
tag = d.get('tag_name', '')
print(f'TAG={tag}')
for a in d.get('assets', []):
    n, u = a.get('name',''), a.get('browser_download_url','')
    if n.endswith('-linux-amd64.deb'): print(f'DEB_URL={u}')
    elif n.endswith('-linux-x86_64.rpm'): print(f'RPM_URL={u}')
    elif n.endswith('-linux-x86_64.AppImage'): print(f'APPIMAGE_URL={u}')
")"
VER="${WANT_VER:-${TAG#v}}"
[ -n "${DEB_URL:-}${RPM_URL:-}${APPIMAGE_URL:-}" ] || { echo "Could not resolve Linux assets for ${TAG}" >&2; exit 1; }

# --- detect distro family ---
# shellcheck disable=SC1091
[ -f /etc/os-release ] && . /etc/os-release
FAMILY="$(echo "${ID_LIKE:-$ID}" | tr '[:upper:]' '[:lower:]')"

if [ "$CHECK" = 1 ]; then
  echo "distro: ${PRETTY_NAME:-$ID} (ID=$ID LIKE=${ID_LIKE:-none})"
  echo "version: $VER ($TAG)"
  echo "deb: ${DEB_URL:-n/a}"
  echo "rpm: ${RPM_URL:-n/a}"
  echo "appimage: ${APPIMAGE_URL:-n/a}"
  case "$FAMILY" in
    *arch*) echo "plan: pacman repo [$REPO_ID] -> $PKG (auto-updates via paru -Syu)" ;;
    *debian*|*ubuntu*) echo "plan: APT repo [$REPO_ID] -> bitchord (auto-updates via apt upgrade)" ;;
    *fedora*|*rhel*|*centos*|*rocky*|*alma*) echo "plan: YUM repo [$REPO_ID] (auto-updates via dnf upgrade)" ;;
    *suse*|*opensuse*) echo "plan: YUM repo [$REPO_ID] (auto-updates via zypper dup)" ;;
    *) echo "plan: AppImage -> ~/.local/bin/$APPIMAGE_NAME" ;;
  esac
  exit 0
fi

SUDO="sudo"
command -v sudo >/dev/null 2>&1 || SUDO="pkexec"

case "$FAMILY" in
  *arch*)
    if ! grep -q "^\[$REPO_ID\]" /etc/pacman.conf 2>/dev/null; then
      # shellcheck disable=SC2002
      printf '\n[%s]\nSigLevel = Optional TrustAll\nServer = %s\n' "$REPO_ID" "$REPO_SERVER" \
        | $SUDO tee -a /etc/pacman.conf >/dev/null
    fi
    if command -v paru >/dev/null 2>&1; then
      [ "$ASSUME_YES" = 1 ] && paru --noconfirm -Sy "$PKG" || paru -Sy "$PKG"
    else
      [ "$ASSUME_YES" = 1 ] && $SUDO pacman --noconfirm -Sy "$PKG" || $SUDO pacman -Sy "$PKG"
    fi
    ;;
  *debian*|*ubuntu*)
    for t in apt-get dpkg-deb; do need "$t"; done
    curl -fsSL "${REPO_RAW}/bitchord.sources" | $SUDO tee /etc/apt/sources.list.d/bitchord.sources >/dev/null
    $SUDO apt-get update
    # exact package name comes from our own Packages metadata (generated from the real .deb)
    DEB_PKG=$(curl -fsSL "${REPO_SERVER}/Packages" | grep -m1 '^Package:' | cut -d' ' -f2)
    [ "$ASSUME_YES" = 1 ] && $SUDO apt-get install -y "$DEB_PKG" || $SUDO apt-get install "$DEB_PKG"
    ;;
  *fedora*|*rhel*|*centos*|*rocky*|*alma*|*suse*|*opensuse*)
    curl -fsSL "${REPO_RAW}/bitchord.repo" | $SUDO tee /etc/yum.repos.d/bitchord.repo >/dev/null
    if command -v dnf >/dev/null 2>&1; then
      [ "$ASSUME_YES" = 1 ] && $SUDO dnf install -y bitchord || $SUDO dnf install bitchord
    elif command -v zypper >/dev/null 2>&1; then
      [ "$ASSUME_YES" = 1 ] && $SUDO zypper --non-interactive install bitchord || $SUDO zypper install bitchord
    else
      [ "$ASSUME_YES" = 1 ] && $SUDO yum install -y bitchord || $SUDO yum install bitchord
    fi
    ;; 
  *)
    dest="${HOME}/.local/bin/${APPIMAGE_NAME}"
    mkdir -p "$(dirname "$dest")"
    curl -fL -o "$dest" "$APPIMAGE_URL"
    chmod +x "$dest"
    mkdir -p "${HOME}/.local/share/applications"
    cat > "${HOME}/.local/share/applications/bitchord.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=BitChord
Exec=$dest
Icon=bitchord
Categories=AudioVideo;Audio;Player;Music;
Terminal=false
EOF2
    echo "Installed AppImage to $dest"
    ;;
esac
echo "Done: BitChord $VER"
