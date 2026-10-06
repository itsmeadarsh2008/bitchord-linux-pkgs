# Maintainer: itsmeadarsh2008 <https://github.com/itsmeadarsh2008>
pkgname=bitchord-bin
pkgver=1.8
pkgrel=2
pkgdesc="Modern YouTube Music client with Apple Music-inspired aesthetics (desktop beta)"
arch=('x86_64')
url="https://github.com/kushagrasinghx/BitChord"
license=('GPL-3.0-only')
depends=('gtk3' 'alsa-lib' 'libxtst' 'libxxf86vm' 'glib2' 'hicolor-icon-theme' 'xdg-utils' 'freetype2' 'libx11')
provides=('bitchord')
conflicts=('bitchord')
options=('!debug')
source=("BitChord-${pkgver}-linux-amd64.deb::https://github.com/kushagrasinghx/BitChord/releases/download/v${pkgver}/BitChord-${pkgver}-linux-amd64.deb"
        "bitchord.desktop")
sha256sums=('b5ac5b568015720ada47f378263e83c7dd6d8232d95fc26ddeb4bd1651db1a54'
           'SKIP')

package() {
  local _data
  _data=$(bsdtar -tf "${srcdir}/BitChord-${pkgver}-linux-amd64.deb" | grep -m1 '^data.tar')
  bsdtar -O -xf "${srcdir}/BitChord-${pkgver}-linux-amd64.deb" "${_data}" | bsdtar -x -C "${pkgdir}"
  # upstream deb ships only /opt/bitchord — add launcher integration
  install -Dm644 "${srcdir}/bitchord.desktop" "${pkgdir}/usr/share/applications/bitchord.desktop"
  install -Dm644 "${pkgdir}/opt/bitchord/lib/BitChord.png" "${pkgdir}/usr/share/pixmaps/bitchord.png"
  mkdir -p "${pkgdir}/usr/bin"
  ln -s /opt/bitchord/bin/BitChord "${pkgdir}/usr/bin/bitchord"
}
