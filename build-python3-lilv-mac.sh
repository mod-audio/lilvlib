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
export CFLAGS="-I/usr/local/include -I$(python3-config --configdir)/../site-packages/numpy/core/include"
export CXXFLAGS="-I/usr/local/include -I$(python3-config --configdir)/../site-packages/numpy/core/include"
export CPPFLAGS=""
export LDFLAGS=""
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig"

mkdir -p "$BASEDIR"
cd "$BASEDIR"

# -------------------------------------------------------------------------------------------
# Get code

if [ ! -d lv2 ]; then
  git clone git://github.com/drobilla/lv2
  cd lv2 &&
      git reset --hard 0713986dcd50195c81675d5819e1cf6658a38fee &&
      cd ..
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
      git reset --hard 83de3f80ca6cbbaac35c003bba9d6625db525939 &&
      cd ..
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

# sed -i -e "s/bld.add_post_fun(autowaf.run_ldconfig)//" */wscript

# -------------------------------------------------------------------------------------------
# Build dependency code

if [ ! -f lv2/build-done ]; then
  cd lv2
  python3 ./waf configure --prefix=/usr/local --no-plugins --copy-headers
  python3 ./waf build
  sudo python3 ./waf install
  sudo cp -r schemas.lv2 /usr/local/lib/lv2/
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
