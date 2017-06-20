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
  git clone http://github.com/drobilla/lv2
  cd lv2 &&
      git reset --hard 0713986dcd50195c81675d5819e1cf6658a38fee &&
      cd ..
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
  cd serd &&
      git reset --hard 83de3f80ca6cbbaac35c003bba9d6625db525939 &&
      cd ..
  sed -i "s|Libs: -L\${libdir} -l@LIB_SERD@|Libs: -L\${libdir} -l@LIB_SERD@ -lm|" serd/serd.pc.in
fi

if [ ! -d sord ]; then
  git clone http://git.drobilla.net/sord.git sord
  cd sord &&
      git reset --hard 31ea384f24e12778d6e30cc7a30b0f48f3d50523 &&
      cd ..
fi

if [ ! -d sratom ]; then
  git clone http://git.drobilla.net/sratom.git sratom
  cd sratom &&
      git reset --hard f62a6d15cb63ffe266ec3cd133245df8947191b2 &&
      cd ..
fi

if [ ! -d lilv ]; then
  git clone http://git.drobilla.net/lilv.git lilv
  cd lilv &&
      git reset --hard 23293be2f10fd64ff85eddb50b6aa381694fa3a3 &&
      cd ..
fi

sed -i "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

# -------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  cd lv2
  python3 ./waf configure --prefix="$PREFIX" --no-plugins --copy-headers
  python3 ./waf build
  python3 ./waf install
  cp -r schemas.lv2 "$PREFIX"/lib/lv2/
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
  python3 ./waf configure --prefix="$PREFIX" --static --static-progs --no-shared --no-utils --no-bash-completion
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
