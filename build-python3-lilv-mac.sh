#!/bin/bash

set -e

# -------------------------------------------------------------------------------------------
# Check dependencies

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

# -------------------------------------------------------------------------------------------
# Prepare environment

export OLDDIR=$(pwd)
export BASEDIR="/tmp/python3-lilv-build"
export TARGETDIR="$(pwd)/macos-build"
export PREFIX="$BASEDIR/system"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"

export CFLAGS="-fPIC -O0 -g -DDEBUG -I$PREFIX/include -I/usr/local/lib/python3.5/site-packages/numpy/core/include"
export CXXFLAGS="-fPIC -O0 -g -DDEBUG -I$PREFIX/include -I/usr/local/lib/python3.5/site-packages/numpy/core/include"
export CPPFLAGS=""
export LDFLAGS="-L$PREFIX/lib"
# "-ldl -lm"

mkdir -p "$BASEDIR"
cd "$BASEDIR"

# -------------------------------------------------------------------------------------------
# Get code

if [ ! -d lv2 ]; then
  git clone --depth 1 git://github.com/drobilla/lv2
  cd lv2 && patch -p1 -i "$OLDDIR"/lv2-plugin-is-project.patch; cd ..
fi

if [ ! -d mod-sdk ]; then
  git clone --depth 1 git://github.com/moddevices/mod-sdk
fi

if [ ! -d kxstudio-ext ]; then
  git clone --depth 1 git://github.com/KXStudio/LV2-Extensions kxstudio-ext
fi

if [ ! -d serd ]; then
  git clone http://git.drobilla.net/serd.git serd
#   sed -i -e "s|Libs: -L\${libdir} -l@LIB_SERD@|Libs: -L\${libdir} -l@LIB_SERD@ -lm|" serd/serd.pc.in
fi

if [ ! -d sord ]; then
  git clone http://git.drobilla.net/sord.git sord
fi

if [ ! -d sratom ]; then
  git clone http://git.drobilla.net/sratom.git sratom
fi

if [ ! -d lilv ]; then
  git clone http://git.drobilla.net/lilv.git lilv
#   cd lilv
#   patch -p1 -i "$OLDDIR/python3-lilv-pkg/debian/patches/fix-link.patch"
#   sed -i -e "s/'-static', '-Wl,--start-group'//" wscript
#   cd ..
fi

sed -i -e "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

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
  python3 ./waf configure --prefix="$PREFIX" --no-utils
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sord/build-done ]; then
  cd sord
  python3 ./waf configure --prefix="$PREFIX"
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sratom/build-done ]; then
  cd sratom
  python3 ./waf configure --prefix="$PREFIX"
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f lilv/build-done ]; then
  cd lilv
  python3 ./waf configure --prefix="$PREFIX" --no-utils
  python3 ./waf build
  python3 ./waf install
  touch build-done
  cd ..
fi

# sed -i -e "s/-lserd-0/-lserd-0 -ldl -lm/" "$PKG_CONFIG_PATH"/serd-0.pc
# sed -i -e "s/-llilv-0/-llilv-0 -lsratom-0 -lsord-0 -lserd-0 -ldl -lm/" "$PKG_CONFIG_PATH"/lilv-0.pc

if [ ! -f lilv/py-build-done ]; then
  cd lilv
  python3 ./waf clean
  python3 ./waf configure --prefix=/usr/local --bindings
  python3 ./waf build
  python3 ./waf install --destdir="$TARGETDIR"
  touch build-done
  cd ..
fi

install -d "$TARGETDIR/usr/local/bin"
install -d "$TARGETDIR/opt/mod/bin"
install -d "$TARGETDIR/opt/mod/lib/lv2"

install -m 755 "$OLDDIR"/sord_validate_mod "$TARGETDIR/usr/local/bin"
install -m 755 $PREFIX/bin/sord_validate "$TARGETDIR/opt/mod/bin"

cp -r $PREFIX/lib/lv2/* "$TARGETDIR/opt/mod/lib/lv2"

# -------------------------------------------------------------------------------------------
# Cleanup

rm -rf "$BASEDIR"

# -------------------------------------------------------------------------------------------
