#!/bin/bash

set -e

# -------------------------------------------------------------------------------------------
# Check dependencies

# sudo apt-get install --no-install-recommends debhelper devscripts dpkg-dev git pkg-config python3-all-dev python3-numpy subversion swig

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

if (which svn > /dev/null); then true; else
  echo "svn not found, please install it"
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

# -------------------------------------------------------------------------------------------
# Prepare environment

export OLDDIR=$(pwd)
export BASEDIR="/tmp/python3-lilv-build"
export PREFIX="$BASEDIR/system"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"

export CFLAGS="-fPIC -O0 -g -DDEBUG"
export CXXFLAGS="-fPIC -O0 -g -DDEBUG"
export CPPFLAGS=""
export LDFLAGS="-ldl -lm"

mkdir -p "$BASEDIR"
cd "$BASEDIR"

# -------------------------------------------------------------------------------------------
# Get code

if [ ! -d lv2 ]; then
  git clone --depth 1 git://github.com/falkTX/lv2
fi

if [ ! -d mod-sdk ]; then
  git clone --depth 1 git://github.com/moddevices/mod-sdk
fi

if [ ! -d serd ]; then
  svn co http://svn.drobilla.net/serd/trunk serd
fi

if [ ! -d sord ]; then
  svn co http://svn.drobilla.net/sord/trunk sord
fi

if [ ! -d sratom ]; then
  svn co http://svn.drobilla.net/lad/trunk/sratom sratom
fi

if [ ! -d lilv ]; then
  svn co http://svn.drobilla.net/lad/trunk/lilv lilv
fi

sed -i "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

# -------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  cd lv2
  python3 ./waf configure --prefix="$PREFIX" --no-plugins
  python3 ./waf build
  python3 ./waf install

  # LV2 needs to be installed system-wide as well
  python3 ./waf clean
  python3 ./waf configure --prefix=/usr --no-plugins
  python3 ./waf build
  sudo python3 ./waf install
  sudo cp -r lv2/lv2plug.in/ns/meta /usr/lib/lv2/
  sudo cp -r ../mod-sdk/*.lv2       /usr/lib/lv2/

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
  patch -p0 -i "$OLDDIR/python3-lilv-pkg/debian/patches/sord-crash-fix.patch"
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
rm -rf * .* || true
mv ../debian .

# -------------------------------------------------------------------------------------------
