#!/bin/bash

set -e

# -------------------------------------------------------------------------------------------
# Check dependencies

# sudo apt-get install --no-install-recommends debhelper devscripts dpkg-dev git pkg-config python3-all-dev python3-numpy subversion swig libpcre3-dev

if (which debuild > /dev/null); then true; else
  echo "debuild not found, please install it"
  exit
fi

if (which git > /dev/null); then true; else
  echo "git not found, please install it"
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

if (which swig > /dev/null); then true; else
  echo "swig not found, please install it"
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

if (dpkg -l | grep python3-numpy > /dev/null); then true; else
  echo "python3-numpy not installed, please install it"
  exit
fi

if (pkg-config --exists libpcre); then true; else
  echo "libpcre-dev not installed, please install it"
  exit
fi

# -------------------------------------------------------------------------------------------
# Prepare environment

export OLDDIR=$(pwd)
export BASEDIR="/tmp/python3-lilv-build"
export PREFIX="$BASEDIR/system"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"

export CFLAGS="-fPIC -O2 -mtune=generic"
export CXXFLAGS="-fPIC -O2 -mtune=generic"
export CPPFLAGS=""
export LDFLAGS="-ldl -lm"

mkdir -p "$BASEDIR"
cd "$BASEDIR"

# -------------------------------------------------------------------------------------------
# Get code

if [ ! -d lv2 ]; then
  git clone --depth 1 git://github.com/drobilla/lv2
  patch -p1 -d lv2 -i "$OLDDIR"/lv2-plugin-is-project.patch
fi

if [ ! -d mod-sdk ]; then
  git clone --depth 1 git://github.com/moddevices/mod-sdk
fi

if [ ! -d kxstudio-ext ]; then
  git clone --depth 1 git://github.com/KXStudio/LV2-Extensions kxstudio-ext
fi

if [ ! -d serd ]; then
  git clone http://git.drobilla.net/serd.git serd
  sed -i "s|Libs: -L\${libdir} -l@LIB_SERD@|Libs: -L\${libdir} -l@LIB_SERD@ -lm|" serd/serd.pc.in
  # NOTE: need to remove this patch when it's applied upstream
  patch -p1 -d serd -i "$OLDDIR"/serd-fix-unitialized-read-error.patch
fi

if [ ! -d sord ]; then
  git clone http://git.drobilla.net/sord.git sord
fi

if [ ! -d sratom ]; then
  git clone http://git.drobilla.net/sratom.git sratom
fi

if [ ! -d lilv ]; then
  git clone http://git.drobilla.net/lilv.git lilv
fi

sed -i "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

# -------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  cd lv2
  python3 ./waf configure --prefix="$PREFIX" --no-plugins --copy-headers
  python3 ./waf build
  python3 ./waf install
  cp -r schemas.lv2 lv2/lv2plug.in/ns/meta "$PREFIX"/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f mod-sdk/build-done ]; then
  cd mod-sdk
  cp -r *.lv2 "$PREFIX"/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f kxstudio-ext/build-done ]; then
  cd kxstudio-ext
  cp -r kx-meta *.lv2 "$PREFIX"/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f serd/build-done ]; then
  cd serd
  python3 ./waf configure --prefix="$PREFIX" --static --no-shared --no-utils
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sord/build-done ]; then
  cd sord
  python3 ./waf configure --prefix="$PREFIX" --static --no-shared
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sratom/build-done ]; then
  cd sratom
  python3 ./waf configure --prefix="$PREFIX" --static --no-shared
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f lilv/build-done ]; then
  cd lilv
  python3 ./waf configure --prefix="$PREFIX" --static --static-progs --no-shared --no-utils
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

sed -i "s/-lserd-0/-lserd-0 -ldl -lm/" "$PKG_CONFIG_PATH"/serd-0.pc
sed -i "s/-llilv-0/-llilv-0 -lsratom-0 -lsord-0 -lserd-0 -ldl -lm/" "$PKG_CONFIG_PATH"/lilv-0.pc

# -------------------------------------------------------------------------------------------
# Build package

cd "$OLDDIR/python3-lilv-pkg"
cp -r "$BASEDIR"/lilv/* .
patch -p1 -i debian/patches/fix-link.patch
debuild clean
debuild binary
debuild clean

# -------------------------------------------------------------------------------------------
# Cleanup

rm -rf "$BASEDIR"

cd "$OLDDIR/python3-lilv-pkg"
mv debian ..
rm -rf *
mv ../debian .

# -------------------------------------------------------------------------------------------
