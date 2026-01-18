#!/usr/bin/env python3

import lilv
import lilvlib
import os
import sys

world = lilv.World()

if len(sys.argv) > 1:
    world.load_specifications()
    world.load_plugin_classes()
    for bundle in sys.argv[1:]:
        if not bundle.endswith(os.sep):
            bundle += os.sep
        world.load_bundle(world.new_file_uri(None, bundle))
else:
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
        print("----------------------", str(plugin.get_uri()), "----------------------")
        print('\t -> ' + '\n\t -> '.join(errors))
