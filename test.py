#!/usr/bin/env python3

import lilv
import lilvlib

world = lilv.World()
world.load_all()

for plugin in world.get_all_plugins():
    info = lilvlib.get_plugin_info(world, plugin)
    if not info['errors']:
        continue

    errors = info['errors'].copy()

    if 'plugin comment is missing' in errors:
        errors.remove('plugin comment is missing')

    if 'plugin license is missing' in errors:
        errors.remove('plugin license is missing')

    if 'plugin is missing version information' in errors:
        errors.remove('plugin is missing version information')

    if errors:
        print("----------------------", str(plugin.get_uri()))
        print(errors)
