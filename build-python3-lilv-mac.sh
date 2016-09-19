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
export CFLAGS="-I/usr/local/include -I/usr/local/lib/python3.5/site-packages/numpy/core/include"
export CXXFLAGS="-I/usr/local/include -I/usr/local/lib/python3.5/site-packages/numpy/core/include"
export CPPFLAGS=""
export LDFLAGS=""
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig"

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
  cd serd &&
      git reset --hard 0688460b2ffd4d85fddda80fb1c3bd408335f9d7 &&
      cd ..
fi

if [ ! -d sord ]; then
  git clone http://git.drobilla.net/sord.git sord
  cd sord &&
      git reset --hard 1bf91df7efb71339b98f27cb88487f0ddd23cde8 &&
      cd ..
fi

if [ ! -d sratom ]; then
  git clone http://git.drobilla.net/sratom.git sratom
  cd sratom &&
      git reset --hard cc233a05de0690001ee2d067531bcc06248b751b &&
      cd ..
fi

if [ ! -d lilv ]; then
  git clone http://git.drobilla.net/lilv.git lilv
  cd lilv &&
      git reset --hard 23293be2f10fd64ff85eddb50b6aa381694fa3a3 &&
      cd ..
fi

# sed -i -e "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

# -------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  cd lv2
  python3 ./waf configure --prefix=/usr/local --no-plugins --copy-headers
  python3 ./waf build
  sudo python3 ./waf install
  sudo cp -r schemas.lv2 /usr/local/lib/lv2/
  sudo cp -r lv2/lv2plug.in/ns/meta /usr/local/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f mod-sdk/build-done ]; then
  cd mod-sdk
  sudo cp -r *.lv2 /usr/local/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f kxstudio-ext/build-done ]; then
  cd kxstudio-ext
  sudo cp -r kx-meta *.lv2 /usr/local/lib/lv2/
  touch build-done
  cd ..
fi

if [ ! -f serd/build-done ]; then
  cd serd
  python3 ./waf configure --prefix=/usr/local --no-utils
  python3 ./waf build
  sudo python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sord/build-done ]; then
  cd sord
  python3 ./waf configure --prefix=/usr/local
  python3 ./waf build
  sudo python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f sratom/build-done ]; then
  cd sratom
  python3 ./waf configure --prefix=/usr/local
  python3 ./waf build
  sudo python3 ./waf install
  touch build-done
  cd ..
fi

if [ ! -f lilv/build-done ]; then
  cd lilv
  python3 ./waf configure --prefix=/usr/local --bindings
  python3 ./waf build
  sudo python3 ./waf install
  touch build-done
  cd ..
fi

cp "$OLDDIR"/sord_validate_mod sord_validate_lv2
sed -i -e "s|/opt/mod|/usr/local|" sord_validate_lv2
sudo install -m 755 sord_validate_lv2 /usr/local/bin

# -------------------------------------------------------------------------------------------
# Cleanup

cd "$OLDDIR"
rm -rf "$BASEDIR"

# -------------------------------------------------------------------------------------------
