#!/bin/bash

set -e

cd "$(dirname ${0})"

# ---------------------------------------------------------------------------------------------------------------------
# Check dependencies

# sudo apt-get install --no-install-recommends debhelper devscripts dpkg-dev git meson pkg-config python3-all-dev subversion libpcre3-dev

if (which debuild > /dev/null); then true; else
  echo "debuild not found, please install it"
  exit
fi

if (which git > /dev/null); then true; else
  echo "git not found, please install it"
  exit
fi

if (which meson > /dev/null); then true; else
  echo "meson not found, please install it"
  exit
fi

if (which pkg-config > /dev/null); then true; else
  echo "pkg-config not found, please install it"
  exit
fi

if (which python3 > /dev/null); then true; else
  echo "python3 not found, please install it"
  exit
fi

if (dpkg -l | grep debhelper > /dev/null); then true; else
  echo "debhelper not installed, please install it"
  exit
fi

if (dpkg -l | grep dpkg-dev > /dev/null); then true; else
  echo "dpkg-dev not installed, please install it"
  exit
fi

if (dpkg -l | grep python3-all-dev > /dev/null); then true; else
  echo "python3-all-dev not installed, please install it"
  exit
fi

if (pkg-config --exists libpcre); then true; else
  echo "libpcre-dev not installed, please install it"
  exit
fi

# ---------------------------------------------------------------------------------------------------------------------
# Prepare environment

export OLDDIR=$(pwd)
export BASEDIR="/tmp/python3-lilv-build"
export PREFIX="${BASEDIR}/system/opt/lilvlib"
export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig"

export CFLAGS="-fPIC -O2 -mtune=generic"
export CXXFLAGS="-fPIC -O2 -mtune=generic"
export CPPFLAGS=""
export LDFLAGS=""

export LC_ALL="C"

rm -rf "${BASEDIR}"
rm -rf "${OLDDIR}/python3-lilv-pkg/system"

mkdir -p "${BASEDIR}"
cd "${BASEDIR}"

# ---------------------------------------------------------------------------------------------------------------------
# Get code

if [ ! -d lv2 ]; then
  git clone https://github.com/lv2/lv2.git
  git -C lv2 reset --hard 86a8bb5d103f749017e6288dbce9bbe981ed9955
  patch -p1 -d lv2 -i "${OLDDIR}"/lv2-plugin-is-project.patch
fi

if [ ! -d darkglass-lv2-extensions ]; then
  git clone --depth 1 https://github.com/Darkglass-Electronics/LV2-Extensions.git darkglass-lv2-extensions
fi

if [ ! -d kxstudio-lv2-extensions ]; then
  git clone --depth 1 https://github.com/KXStudio/LV2-Extensions.git kxstudio-lv2-extensions
fi

if [ ! -d mod-lv2-extensions ]; then
  git clone --depth 1 https://github.com/mod-audio/mod-lv2-extensions.git
fi

if [ ! -d zix ]; then
  git clone https://github.com/drobilla/zix.git zix
  git -C zix reset --hard 9a2af45aef5d782a3ab0cd52065894f281629055
fi

if [ ! -d serd ]; then
  git clone https://github.com/drobilla/serd.git serd
  git -C serd reset --hard 1fd12ee91b4dfc124ce4435b1fe52b3a69c75255
#   sed -i "s|Libs: -L\${libdir} -l@LIB_SERD@|Libs: -L\${libdir} -l@LIB_SERD@ -lm|" serd/serd.pc.in
fi

if [ ! -d sord ]; then
  git clone https://github.com/drobilla/sord.git sord
  git -C sord reset --hard 5458be87a898a658985248b4178ae5cfd13696ea
fi

if [ ! -d sratom ]; then
  git clone https://github.com/lv2/sratom.git sratom
  git -C sratom reset --hard 0dee0bed63f2fe4d8178b9fe6482d1c686a39b0c
fi

if [ ! -d lilv ]; then
  git clone https://github.com/lv2/lilv.git lilv
  git -C lilv reset --hard 2868c482df9b58bde4934a925456e50114cdcc25
fi

# ---------------------------------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  pushd lv2
  meson setup build \
    --reconfigure \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Ddocs=disabled \
    -Dbundles=true \
    -Dheaders=true \
    -Dlint=false \
    -Dold_headers=true \
    -Dtests=disabled \
    -Dtools=enabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

if [ ! -f darkglass-lv2-extensions/build-done ]; then
  pushd darkglass-lv2-extensions
  cp -rv dg-meta *.lv2 "${PREFIX}/lib/lv2/"
  touch build-done
  popd
fi

if [ ! -f kxstudio-lv2-extensions/build-done ]; then
  pushd kxstudio-lv2-extensions
  cp -rv kx-meta *.lv2 "${PREFIX}/lib/lv2/"
  touch build-done
  popd
fi

if [ ! -f mod-lv2-extensions/build-done ]; then
  pushd mod-lv2-extensions
  cp -rv *.lv2 "${PREFIX}/lib/lv2/"
  touch build-done
  popd
fi

if [ ! -f zix/build-done ]; then
  pushd zix
  meson setup build \
    --reconfigure \
    -Ddefault_library=static \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Dbenchmarks=disabled \
    -Ddocs=disabled \
    -Dhtml=disabled \
    -Dlint=false \
    -Dsinglehtml=disabled \
    -Dtests=disabled \
    -Dtests_cpp=disabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

if [ ! -f serd/build-done ]; then
  pushd serd
  meson setup build \
    --reconfigure \
    -Ddefault_library=static \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Ddocs=disabled \
    -Dhtml=disabled \
    -Dlint=false \
    -Dman=disabled \
    -Dman_html=disabled \
    -Dsinglehtml=disabled \
    -Dstatic=true \
    -Dtests=disabled \
    -Dtools=disabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

if [ ! -f sord/build-done ]; then
  pushd sord
  meson setup build \
    --reconfigure \
    -Ddefault_library=static \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Dbindings_cpp=disabled \
    -Ddocs=disabled \
    -Dlint=false \
    -Dman=disabled \
    -Dtests=disabled \
    -Dtools=enabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

if [ ! -f sratom/build-done ]; then
  pushd sratom
  meson setup build \
    --reconfigure \
    -Ddefault_library=static \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Ddocs=disabled \
    -Dhtml=disabled \
    -Dlint=false \
    -Dsinglehtml=disabled \
    -Dtests=disabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

if [ ! -f lilv/build-done ]; then
  pushd lilv
  meson setup build \
    --reconfigure \
    -Ddefault_library=shared \
    -Dlibdir="lib" \
    -Dprefix="${PREFIX}" \
    -Dbindings_cpp=disabled \
    -Dbindings_py=enabled \
    -Ddocs=disabled \
    -Ddynmanifest=disabled \
    -Dhtml=disabled \
    -Dlint=false \
    -Dsinglehtml=disabled \
    -Dtests=disabled \
    -Dtools=disabled
  ninja -C build
  ninja -C build install
  touch build-done
  popd
fi

sed -i -e 's|CDLL("liblilv|CDLL("/opt/lilvlib/lib/liblilv|' "${PREFIX}/lib/python3/dist-packages/lilv.py"
rm -rf "${PREFIX}/lib/python3/dist-packages/__pycache__"

# -------------------------------------------------------------------------------------------
# Build package

pushd "${OLDDIR}/python3-lilv-pkg"

mv "${BASEDIR}/system" system
mkdir -p system/usr/bin
mkdir -p system/usr/lib/python3/dist-packages/lilvlib

install -m 755 ../lv2_validate_mod system/usr/bin/
install -m 644 ../lilvlib/*.py system/usr/lib/python3/dist-packages/lilvlib/

mv system/opt/lilvlib/lib/python3/dist-packages/lilv.py system/usr/lib/python3/dist-packages/

rm -rf system/opt/lilvlib/include
rm -rf system/opt/lilvlib/lib/pkgconfig
rm -rf system/opt/lilvlib/lib/python3
rm -rf system/opt/lilvlib/lib/*.a

fakeroot debian/rules binary
fakeroot debian/rules clean

# if the above commands fail, try these:
# debuild binary
# debuild clean

popd

# -------------------------------------------------------------------------------------------
# Cleanup

rm -rf "${BASEDIR}"
rm -rf "${OLDDIR}/python3-lilv-pkg/system"

# -------------------------------------------------------------------------------------------
