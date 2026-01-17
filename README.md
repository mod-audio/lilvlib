## lilvlib

This repository contains a build script for lilvlib and its python3-lilv dependency, using the latest development version from git.

The reason why you need this script is because most distros have an outdated lilv binary or don't build lilv python modules.

To start simply run:

`./build-python3-lilv.sh`

If you're missing some dependency the script will let you know right at the beginning.


The generated package will contain `python3-lilv` and also everything needed for MOD's LV2 plugin inquisition.
This includes:

- LV2 headers and definitions
- Dargklass LV2 definitions
- KXStudio LV2 definitions
- MOD Audio LV2 definitions
- sord_validate (static binary)
- lv2_validate_mod

The `lv2_validate_mod` is a helper script that runs `lv2_validate` with extra Darkglass, KXStudio and MOD Audio related bundles.

Because this package uses the definitions copied during build (in `/opt`), it does not depend on any external resources.

## Install

Build:

`./build-python3-lilv.sh`

Install
```bash
dpkg -i python3-lilv_0.22.1+git20170620_amd64.deb
```

## Testing

Use

```bash
/usr/bin/python3
```

```python
import lilvlib
lilvlib.get_plugin_info_helper('')
```
