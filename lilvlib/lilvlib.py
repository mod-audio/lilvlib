#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------------------------------
# Imports

import json
import lilv
import os

from math import fmod

# ------------------------------------------------------------------------------------------------------------
# Definitions

PREFIX_INGEN    = "http://drobilla.net/ns/ingen#"
PREFIX_LV2CORE  = "http://lv2plug.in/ns/lv2core#"
PREFIX_MOD      = "http://moddevices.com/ns/mod#"
PREFIX_MODGUI   = "http://moddevices.com/ns/modgui#"
PREFIX_MODPEDAL = "http://moddevices.com/ns/modpedal#"

# ------------------------------------------------------------------------------------------------------------
# Utilities

class NS(object):
    def __init__(self, world, base):
        self.world = world
        self.base = base
        self._cache = {}

    def __getattr__(self, attr):
        if attr.endswith("_"):
            attr = attr[:-1]
        if attr not in self._cache:
            self._cache[attr] = self.world.new_uri(self.base + attr)
        return self._cache[attr]

def is_integer(string):
    return string.strip().lstrip("-+").isdigit()

def first_or(nodes, fallback):
    first = next(iter(nodes), None)
    return first if first is not None else fallback

def int_first_or(nodes):
    first = next(iter(nodes), None)
    return int(first) if first is not None else 0

def str_first_or(nodes):
    if nodes is None:
        return ""
    first = next(iter(nodes), None)
    return str(first) if first is not None else ""

def str_or(node):
    return str(node) if node is not None else ""

def get_short_port_name(portName):
    if len(portName) <= 16:
        return portName

    portName = portName.split("/",1)[0].split(" (",1)[0].split(" [",1)[0].strip()

    # cut stuff if too big
    if len(portName) > 16:
        portName = portName[0] + portName[1:].replace("a","").replace("e","").replace("i","").replace("o","").replace("u","")

        if len(portName) > 16:
            portName = portName[:16]

    return portName.strip()

# ------------------------------------------------------------------------------------------------------------

def get_category(nodes):
    if nodes is None:
        return []

    lv2_category_indexes = {
        'DelayPlugin': ['Delay'],
        'DistortionPlugin': ['Distortion'],
        'WaveshaperPlugin': ['Distortion', 'Waveshaper'],
        'DynamicsPlugin': ['Dynamics'],
        'AmplifierPlugin': ['Dynamics', 'Amplifier'],
        'CompressorPlugin': ['Dynamics', 'Compressor'],
        'ExpanderPlugin': ['Dynamics', 'Expander'],
        'GatePlugin': ['Dynamics', 'Gate'],
        'LimiterPlugin': ['Dynamics', 'Limiter'],
        'FilterPlugin': ['Filter'],
        'AllpassPlugin': ['Filter', 'Allpass'],
        'BandpassPlugin': ['Filter', 'Bandpass'],
        'CombPlugin': ['Filter', 'Comb'],
        'EQPlugin': ['Filter', 'Equaliser'],
        'MultiEQPlugin': ['Filter', 'Equaliser', 'Multiband'],
        'ParaEQPlugin': ['Filter', 'Equaliser', 'Parametric'],
        'HighpassPlugin': ['Filter', 'Highpass'],
        'LowpassPlugin': ['Filter', 'Lowpass'],
        'GeneratorPlugin': ['Generator'],
        'ConstantPlugin': ['Generator', 'Constant'],
        'InstrumentPlugin': ['Generator', 'Instrument'],
        'OscillatorPlugin': ['Generator', 'Oscillator'],
        'ModulatorPlugin': ['Modulator'],
        'ChorusPlugin': ['Modulator', 'Chorus'],
        'FlangerPlugin': ['Modulator', 'Flanger'],
        'PhaserPlugin': ['Modulator', 'Phaser'],
        'ReverbPlugin': ['Reverb'],
        'SimulatorPlugin': ['Simulator'],
        'SpatialPlugin': ['Spatial'],
        'SpectralPlugin': ['Spectral'],
        'PitchPlugin': ['Spectral', 'Pitch Shifter'],
        'UtilityPlugin': ['Utility'],
        'AnalyserPlugin': ['Utility', 'Analyser'],
        'ConverterPlugin': ['Utility', 'Converter'],
        'FunctionPlugin': ['Utility', 'Function'],
        'MixerPlugin': ['Utility', 'Mixer'],
        #'MIDIPlugin': ['MIDI', 'Utility'],
    }
    mod_category_indexes = {
        'DelayPlugin': ['Delay'],
        'DistortionPlugin': ['Distortion'],
        'DynamicsPlugin': ['Dynamics'],
        'FilterPlugin': ['Filter'],
        'GeneratorPlugin': ['Generator'],
        'ModulatorPlugin': ['Modulator'],
        'ReverbPlugin': ['Reverb'],
        'SimulatorPlugin': ['Simulator'],
        'SpatialPlugin': ['Spatial'],
        'SpectralPlugin': ['Spectral'],
        'UtilityPlugin': ['Utility'],
        'MIDIPlugin': ['Utility', 'MIDI'],
        'ControlVoltagePlugin': ['ControlVoltage'],
    }

    def fill_in_lv2_categories(nodes):
        cats = []
        for node in nodes:
            category = str(node).replace(PREFIX_LV2CORE,"")
            if category in lv2_category_indexes.keys():
                cats += lv2_category_indexes[category]
        return cats

    def fill_in_mod_categories(nodes):
        cats = []
        for node in nodes:
            category = str(node).replace(PREFIX_MOD,"")
            if category in mod_category_indexes.keys():
                cats += mod_category_indexes[category]
        return cats

    categories = []

    # find MOD category first, takes precedence
    for cat in fill_in_mod_categories(nodes):
        if cat not in categories:
            categories.append(cat)

    if len(categories) > 0:
        return categories

    for cat in fill_in_lv2_categories(nodes):
        if cat not in categories:
            categories.append(cat)

    return categories

def get_port_data(port, subj):
    return [str(node) for node in port.get_value(subj)]

def get_port_unit(miniuri):
  # using label, render, symbol
  units = {
      's': ["seconds", "%f s", "s"],
      'ms': ["milliseconds", "%f ms", "ms"],
      'min': ["minutes", "%f mins", "min"],
      'bar': ["bars", "%f bars", "bars"],
      'beat': ["beats", "%f beats", "beats"],
      'frame': ["audio frames", "%f frames", "frames"],
      'm': ["metres", "%f m", "m"],
      'cm': ["centimetres", "%f cm", "cm"],
      'mm': ["millimetres", "%f mm", "mm"],
      'km': ["kilometres", "%f km", "km"],
      'inch': ["inches", """%f\"""", "in"],
      'mile': ["miles", "%f mi", "mi"],
      'db': ["decibels", "%f dB", "dB"],
      'pc': ["percent", "%f%%", "%"],
      'coef': ["coefficient", "* %f", "*"],
      'hz': ["hertz", "%f Hz", "Hz"],
      'khz': ["kilohertz", "%f kHz", "kHz"],
      'mhz': ["megahertz", "%f MHz", "MHz"],
      'bpm': ["beats per minute", "%f BPM", "BPM"],
      'oct': ["octaves", "%f octaves", "oct"],
      'cent': ["cents", "%f ct", "ct"],
      'semitone12TET': ["semitones", "%f semi", "semi"],
      'degree': ["degrees", "%f deg", "deg"],
      'midiNote': ["MIDI note", "MIDI note %d", "note"],
      'volts': ["volts", "%f v", "v"],
  }
  if miniuri in units.keys():
      return units[miniuri]
  return ("","","")

# ------------------------------------------------------------------------------------------------------------
# get_bundle_dirname

def get_bundle_dirname(bundleuri):
    world = lilv.World()
    bundle = str(world.new_uri(bundleuri).get_path())

    if not os.path.exists(bundle):
        raise IOError(bundleuri)

    if os.path.isfile(bundle):
        bundle = os.path.dirname(bundle)

    return bundle

# ------------------------------------------------------------------------------------------------------------
# get_pedalboard_info

# Get info from an lv2 bundle
# @a bundle is a string, consisting of a directory in the filesystem (absolute pathname).
def get_pedalboard_info(bundle):
    # lilv wants the last character as the separator
    bundle = os.path.abspath(bundle)
    if not bundle.endswith(os.sep):
        bundle += os.sep

    # Create our own unique lilv world
    # We'll load a single bundle and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    world.load_specifications()
    world.load_plugin_classes()

    # convert bundle string into a lilv node
    bundlenode = world.new_file_uri(None, bundle)

    # load the bundle
    world.load_bundle(bundlenode)

    # get all plugins in the bundle
    plugins = world.get_all_plugins()

    # make sure the bundle includes 1 and only 1 plugin (the pedalboard)
    if len(plugins) != 1:
        raise Exception('get_pedalboard_info(%s) - bundle has 0 or > 1 plugin'.format(bundle))

    plugin = first_or(plugins, None)

    if plugin is None:
        raise Exception('get_pedalboard_info(%s) - failed to get plugin, you are using an old lilv!'.format(bundle))

    # define the needed stuff
    ns_rdf      = NS(world, lilv.LILV_NS_RDF)
    ns_lv2core  = NS(world, lilv.LILV_NS_LV2)
    ns_ingen    = NS(world, PREFIX_INGEN)
    ns_mod      = NS(world, PREFIX_MOD)
    ns_modpedal = NS(world, PREFIX_MODPEDAL)

    # check if the plugin is a pedalboard
    plugin_types = tuple(str(node) for node in plugin.get_value(ns_rdf.type_))

    if "http://moddevices.com/ns/modpedal#Pedalboard" not in plugin_types:
        raise Exception('get_pedalboard_info(%s) - plugin has no mod:Pedalboard type'.format(bundle))

    # let's get all the info now
    ingenarcs   = []
    ingenblocks = []

    info = {
        'name'  : str(plugin.get_name()),
        'uri'   : str(plugin.get_uri()),
        'author': str_or(plugin.get_author_name()), # Might be empty
        'unit': {
            'name': str_first_or(plugin.get_value(ns_modpedal.unitName)),
            'model': str_first_or(plugin.get_value(ns_modpedal.unitModel)),
        },
        'hardware': {
            # we save this info later
            'audio': {
                'ins' : 0,
                'outs': 0
             },
            'cv': {
                'ins' : 0,
                'outs': 0
             },
            'midi': {
                'ins' : 0,
                'outs': 0
             },
        },
        'size': {
            'width' : int_first_or(plugin.get_value(ns_modpedal.width)),
            'height': int_first_or(plugin.get_value(ns_modpedal.height)),
        },
        'screenshot' : os.path.basename(str_first_or(plugin.get_value(ns_modpedal.screenshot))),
        'thumbnail'  : os.path.basename(str_first_or(plugin.get_value(ns_modpedal.thumbnail))),
        'connections': [], # we save this info later
        'plugins'    : [], # we save this info later
    }

    # handle unit name and model for old pedalboards
    if not info['unit']['name']:
        for port in plugin.get_value(ns_lv2core.port):
            if str(port).endswith(("/midi_legacy_mode", "/midi_separated_mode")):
                isDuoX = True
                break
        else:
            isDuoX = False

        if isDuoX:
            info['unit'] = {
              'name': "MOD Duo X",
              'model': "duox:aarch64-a53",
            }
        else:
            info['unit'] = {
              'name': "MOD Duo",
              'model': "duo:arm-a7",
            }

    # connections
    for arc in plugin.get_value(ns_ingen.arc):
        head = world.get(arc, ns_ingen.head, None)
        tail = world.get(arc, ns_ingen.tail, None)

        if head is None or tail is None:
            continue

        ingenarcs.append({
            "source": tail.get_path().replace(bundle,"",1),
            "target": head.get_path().replace(bundle,"",1)
        })

    # hardware ports
    handled_port_uris = []
    for port in plugin.get_value(ns_lv2core.port):
        # check if we already handled this port
        port_uri = str(port)
        if port_uri in handled_port_uris:
            continue
        if port_uri.endswith("/control_in") or port_uri.endswith("/control_out"):
            continue
        handled_port_uris.append(port_uri)

        # get types
        port_types = world.find_nodes(port, ns_rdf.type_, None)

        if port_types is None:
            continue

        portDir  = "" # input or output
        portType = "" # atom, audio or cv

        for port_type in port_types:
            port_type_uri = str(port_type)

            if port_type_uri == (PREFIX_LV2CORE + "InputPort"):
                portDir = "input"
            elif port_type_uri == (PREFIX_LV2CORE + "OutputPort"):
                portDir = "output"
            elif port_type_uri == (PREFIX_LV2CORE + "AudioPort"):
                portType = "audio"
            elif port_type_uri in ((PREFIX_LV2CORE + "CVPort"), (PREFIX_MOD + "CVPort")):
                portType = "cv"
            elif port_type_uri == "http://lv2plug.in/ns/ext/atom#AtomPort":
                portType = "atom"

        if not (portDir or portType):
            continue

        if portType == "audio":
            if portDir == "input":
                info['hardware']['audio']['ins'] += 1
            else:
                info['hardware']['audio']['outs'] += 1

        elif portType == "atom":
            if portDir == "input":
                info['hardware']['midi']['ins'] += 1
            else:
                info['hardware']['midi']['outs'] += 1

        elif portType == "cv":
            if portDir == "input":
                info['hardware']['cv']['ins'] += 1
            else:
                info['hardware']['cv']['outs'] += 1

    # plugins
    for block in plugin.get_value(ns_ingen.block):
        protouri1 = world.get(block, ns_lv2core.prototype, None)
        protouri2 = world.get(block, ns_ingen.prototype, None)

        if protouri1 is not None:
            proto = protouri1
        elif protouri2 is not None:
            proto = protouri2
        else:
            continue

        instance = block.get_path().replace(bundle,"",1)
        uri      = str(proto)

        x        = world.get(block, ns_ingen.canvasX, None)
        y        = world.get(block, ns_ingen.canvasY, None)
        enabled  = world.get(block, ns_ingen.enabled, None)
        builder  = world.get(block, ns_mod.builderVersion, None)
        release  = world.get(block, ns_mod.releaseNumber, None)
        minorver = world.get(block, ns_lv2core.minorVersion, None)
        microver = world.get(block, ns_lv2core.microVersion, None)
        buildId  = world.get(block, ns_mod.buildId, None)
        buildEnv = world.get(block, ns_mod.buildEnvironment, None)

        ingenblocks.append({
            "instance": instance,
            "uri"     : uri,
            "x"       : float(x),
            "y"       : float(y),
            "enabled" : bool(enabled) if enabled is not None else False,
            "builder" : int(builder) if builder is not None else 0,
            "release" : int(release) if release is not None else 0,
            "minorVersion": int(minorver) if minorver is not None else 0,
            "microVersion": int(microver) if microver is not None else 0,
            "buildId"         : str(buildId) if buildId is not None else "",
            "buildEnvironment": str(buildEnv) if buildEnv is not None else "",
        })

    info['connections'] = ingenarcs
    info['plugins']     = ingenblocks

    return info

# ------------------------------------------------------------------------------------------------------------
# get_pedalboard_name

# Faster version of get_pedalboard_info when we just need to know the pedalboard name
# @a bundle is a string, consisting of a directory in the filesystem (absolute pathname).
def get_pedalboard_name(bundle):
    # lilv wants the last character as the separator
    bundle = os.path.abspath(bundle)
    if not bundle.endswith(os.sep):
        bundle += os.sep

    # Create our own unique lilv world
    # We'll load a single bundle and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    world.load_specifications()
    world.load_plugin_classes()

    # convert bundle string into a lilv node
    bundlenode = world.new_file_uri(None, bundle)

    # load the bundle
    world.load_bundle(bundlenode)

    # get all plugins in the bundle
    plugins = world.get_all_plugins()

    # make sure the bundle includes 1 and only 1 plugin (the pedalboard)
    if len(plugins) != 1:
        raise Exception('get_pedalboard_info(%s) - bundle has 0 or > 1 plugin'.format(bundle))

    plugin = first_or(plugins, None)

    if plugin is None:
        raise Exception('get_pedalboard_info(%s) - failed to get plugin'.format(bundle))

    # define the needed stuff
    ns_rdf = NS(world, lilv.LILV_NS_RDF)

    # check if the plugin is a pedalboard
    plugin_types = tuple(str(node) for node in plugin.get_value(ns_rdf.type_))

    if "http://moddevices.com/ns/modpedal#Pedalboard" not in plugin_types:
        raise Exception('get_pedalboard_info(%s) - plugin has no mod:Pedalboard type'.format(bundle))

    return str(plugin.get_name())

# ------------------------------------------------------------------------------------------------------------
# plugin_has_modgui

# Check if a plugin has modgui
def plugin_has_modgui(world, plugin):
    # define the needed stuff
    ns_modgui = NS(world, PREFIX_MODGUI)

    # --------------------------------------------------------------------------------------------------------
    # get the proper modgui

    modguigui = None

    for mgui in plugin.get_value(ns_modgui.gui):
        resdir = first_or(world.find_nodes(mgui, ns_modgui.resourcesDirectory, None), None)
        if resdir is None:
            continue
        modguigui = mgui
        if resdir.get_path().startswith(os.path.expanduser("~")):
            # found a modgui in the home dir, stop here and use it
            break

    # --------------------------------------------------------------------------------------------------------
    # check selected modgui

    if modguigui is None:
        return False

    # resourcesDirectory *must* be present
    modgui_resdir = first_or(world.find_nodes(modguigui, ns_modgui.resourcesDirectory, None), None)

    if modgui_resdir is None:
        return False

    return os.path.exists(modgui_resdir.get_path())

# ------------------------------------------------------------------------------------------------------------
# get_plugin_info

# Get info from a lilv plugin
# This is used in get_plugins_info below and MOD-SDK
def get_plugin_info(world, plugin, useAbsolutePath = True):
    # define the needed stuff
    ns_doap    = NS(world, lilv.LILV_NS_DOAP)
    ns_foaf    = NS(world, lilv.LILV_NS_FOAF)
    ns_rdf     = NS(world, lilv.LILV_NS_RDF)
    ns_rdfs    = NS(world, lilv.LILV_NS_RDFS)
    ns_lv2core = NS(world, lilv.LILV_NS_LV2)
    ns_atom    = NS(world, "http://lv2plug.in/ns/ext/atom#")
    ns_midi    = NS(world, "http://lv2plug.in/ns/ext/midi#")
    ns_morph   = NS(world, "http://lv2plug.in/ns/ext/morph#")
    ns_pprops  = NS(world, "http://lv2plug.in/ns/ext/port-props#")
    ns_pset    = NS(world, "http://lv2plug.in/ns/ext/presets#")
    ns_units   = NS(world, "http://lv2plug.in/ns/extensions/units#")
    ns_mod     = NS(world, PREFIX_MOD)
    ns_modgui  = NS(world, PREFIX_MODGUI)

    bundleuri = plugin.get_bundle_uri()
    bundle    = bundleuri.get_path()
    bundleuri = str(bundleuri)

    errors   = []
    warnings = []

    # --------------------------------------------------------------------------------------------------------
    # uri

    uri = str(plugin.get_uri())

    if not uri:
        errors.append("plugin uri is missing or invalid")
    elif uri.startswith("file:"):
        errors.append("plugin uri is local, and thus not suitable for redistribution")
    #elif not (uri.startswith("http:") or uri.startswith("https:")):
        #warnings.append("plugin uri is not a real url")

    # --------------------------------------------------------------------------------------------------------
    # name

    name = str(plugin.get_name())

    if not name:
        errors.append("plugin name is missing")

    # --------------------------------------------------------------------------------------------------------
    # binary

    binary = plugin.get_library_uri().get_path()

    if not binary:
        errors.append("plugin binary is missing")
    elif not useAbsolutePath:
        binary = binary.replace(bundle,"",1)

    # --------------------------------------------------------------------------------------------------------
    # license

    licenses = tuple(str(node) for node in plugin.get_value(ns_doap.license))

    if len(licenses) > 0:
        license = sorted(licenses)[0]

    else:
        license = ""
        project = first_or(plugin.get_value(ns_lv2core.project), None)
        if project is not None:
            license = str_first_or(world.get(project, ns_doap.license, None))

    if not license:
        errors.append("plugin license is missing")

    elif license.startswith(bundleuri):
        license = license.replace(bundleuri,"",1)
        warnings.append("plugin license entry is a local path instead of a string")

    # --------------------------------------------------------------------------------------------------------
    # comment

    comment = str_first_or(plugin.get_value(ns_rdfs.comment)).strip()

    # sneaky empty comments!
    if len(comment) > 0 and comment == len(comment) * comment[0]:
        comment = ""

    if not comment:
        errors.append("plugin comment is missing")

    # --------------------------------------------------------------------------------------------------------
    # version

    microver = first_or(plugin.get_value(ns_lv2core.microVersion), None)
    minorver = first_or(plugin.get_value(ns_lv2core.minorVersion), None)

    if microver is None and minorver is None:
        errors.append("plugin is missing version information")
        minorVersion = 0
        microVersion = 0

    else:
        if minorver is None:
            errors.append("plugin is missing minorVersion")
            minorVersion = 0
        else:
            minorVersion = int(minorver)

        if microver is None:
            errors.append("plugin is missing microVersion")
            microVersion = 0
        else:
            microVersion = int(microver)

    version = "%d.%d" % (minorVersion, microVersion)

    # 0.x is experimental
    if minorVersion == 0:
        stability = "experimental"

    # odd x.2 or 2.x is testing/development
    elif minorVersion % 2 != 0 or microVersion % 2 != 0:
        stability = "testing"

    # otherwise it's stable
    else:
        stability = "stable"

    # --------------------------------------------------------------------------------------------------------
    # author

    author = {
        'name'    : str_or(plugin.get_author_name()),
        'homepage': str_or(plugin.get_author_homepage()),
        'email'   : str_or(plugin.get_author_email()),
    }

    if not author['name']:
        errors.append("plugin author name is missing")

    if not author['homepage']:
        prj = first_or(plugin.get_value(ns_lv2core.project), None)
        if prj is not None:
            maintainer = world.get(prj, ns_doap.maintainer, None)
            if maintainer is not None:
                homepage = world.get(maintainer, ns_foaf.homepage, None)
                if homepage is not None:
                    author['homepage'] = str(homepage)

    if not author['homepage']:
        warnings.append("plugin author homepage is missing")

    if not author['email']:
        pass
    elif author['email'].startswith(bundleuri):
        author['email'] = author['email'].replace(bundleuri,"",1)
        warnings.append("plugin author email entry is missing 'mailto:' prefix")
    elif author['email'].startswith("mailto:"):
        author['email'] = author['email'].replace("mailto:","",1)

    # --------------------------------------------------------------------------------------------------------
    # brand

    brand = str_first_or(plugin.get_value(ns_mod.brand))

    if not brand:
        brand = author['name'].split(" - ",1)[0].split(" ",1)[0]
        brand = brand.rstrip(",").rstrip(";")
        if len(brand) > 16:
            brand = brand[:16]
        warnings.append("plugin brand is missing")

    elif len(brand) > 16:
        brand = brand[:16]
        errors.append("plugin brand has more than 16 characters")

    # --------------------------------------------------------------------------------------------------------
    # label

    label = str_first_or(plugin.get_value(ns_mod.label))

    if not label:
        if len(name) <= 24:
            label = name
        else:
            labels = name.split(" - ",1)[0].split(" ")
            if labels[0].lower() in bundle.lower() and len(labels) > 1 and not labels[1].startswith(("(","[")):
                label = labels[1]
            else:
                label = labels[0]

            if len(label) > 24:
                label = label[:24]

            warnings.append("plugin label is missing")

    elif len(label) > 24:
        label = label[:24]
        errors.append("plugin label has more than 24 characters")

    # --------------------------------------------------------------------------------------------------------
    # bundles

    bundles = []

    if useAbsolutePath:
        for bnode in plugin.get_data_uris():
            bpath = os.path.abspath(os.path.dirname(bnode.get_path()))

            if not bpath.endswith(os.sep):
                bpath += os.sep

            if bpath not in bundles:
                bundles.append(bpath)

        if bundle not in bundles:
            bundles.append(bundle)

    # --------------------------------------------------------------------------------------------------------
    # get the proper modgui

    modguigui = None

    for mgui in plugin.get_value(ns_modgui.gui):
        resdir = first_or(world.find_nodes(mgui, ns_modgui.resourcesDirectory, None), None)
        if resdir is None:
            continue
        modguigui = mgui
        if not useAbsolutePath:
            # special build, use first modgui found
            break
        if resdir.get_path().startswith(os.path.expanduser("~")):
            # found a modgui in the home dir, stop here and use it
            break

    # --------------------------------------------------------------------------------------------------------
    # gui

    gui = {}

    if modguigui is None:
        warnings.append("no modgui available")

    else:
        # resourcesDirectory *must* be present
        modgui_resdir = first_or(world.find_nodes(modguigui, ns_modgui.resourcesDirectory, None), None)

        if modgui_resdir is None:
            errors.append("modgui has no resourcesDirectory data")

        else:
            if useAbsolutePath:
                gui['resourcesDirectory'] = modgui_resdir.get_path()

                # check if modgui is defined in a separate file
                gui['usingSeeAlso'] = os.path.exists(os.path.join(bundle, "modgui.ttl"))

                # check if the modgui definition is on its own file and in the user dir
                gui['modificableInPlace'] = bool((bundle not in gui['resourcesDirectory'] or gui['usingSeeAlso']) and
                                                 gui['resourcesDirectory'].startswith(os.path.expanduser("~")))
            else:
                gui['resourcesDirectory'] = str(modgui_resdir).replace(bundleuri,"",1)

            # icon and settings templates
            modgui_icon = first_or(world.find_nodes(modguigui, ns_modgui.iconTemplate, None), None)
            modgui_setts = first_or(world.find_nodes(modguigui, ns_modgui.settingsTemplate, None), None)

            if modgui_icon is None:
                errors.append("modgui has no iconTemplate data")
            else:
                iconFile = modgui_icon.get_path()
                if os.path.exists(iconFile):
                    gui['iconTemplate'] = iconFile if useAbsolutePath else iconFile.replace(bundle,"",1)
                else:
                    errors.append("modgui iconTemplate file is missing")

            if modgui_setts is not None:
                settingsFile = modgui_setts.get_path()
                if os.path.exists(settingsFile):
                    gui['settingsTemplate'] = settingsFile if useAbsolutePath else settingsFile.replace(bundle,"",1)
                else:
                    errors.append("modgui settingsTemplate file is missing")

            # javascript and stylesheet files
            modgui_script = first_or(world.find_nodes(modguigui, ns_modgui.javascript, None), None)
            modgui_style = first_or(world.find_nodes(modguigui, ns_modgui.stylesheet, None), None)

            if modgui_script is not None:
                javascriptFile = modgui_script.get_path()
                if os.path.exists(javascriptFile):
                    gui['javascript'] = javascriptFile if useAbsolutePath else javascriptFile.replace(bundle,"",1)
                else:
                    errors.append("modgui javascript file is missing")

            if modgui_style is None:
                errors.append("modgui has no stylesheet data")
            else:
                stylesheetFile = modgui_style.get_path()
                if os.path.exists(stylesheetFile):
                    gui['stylesheet'] = stylesheetFile if useAbsolutePath else stylesheetFile.replace(bundle,"",1)
                else:
                    errors.append("modgui stylesheet file is missing")

            # template data for backwards compatibility
            # FIXME remove later once we got rid of all templateData files
            modgui_templ = first_or(world.find_nodes(modguigui, ns_modgui.templateData, None), None)

            if modgui_templ is not None:
                warnings.append("modgui is using old deprecated templateData")
                templFile = modgui_templ.get_path()
                if os.path.exists(templFile):
                    with open(templFile, 'r') as fd:
                        try:
                            data = json.loads(fd.read())
                        except:
                            data = {}
                        keys = list(data.keys())

                        if 'author' in keys:
                            gui['brand'] = data['author']
                        if 'label' in keys:
                            gui['label'] = data['label']
                        if 'color' in keys:
                            gui['color'] = data['color']
                        if 'knob' in keys:
                            gui['knob'] = data['knob']
                        if 'controls' in keys:
                            index = 0
                            ports = []
                            for ctrl in data['controls']:
                                ports.append({
                                    'index' : index,
                                    'name'  : ctrl['name'],
                                    'symbol': ctrl['symbol'],
                                })
                                index += 1
                            gui['ports'] = ports

            # screenshot and thumbnail
            modgui_scrn = first_or(world.find_nodes(modguigui, ns_modgui.screenshot, None), None)
            modgui_thumb = first_or(world.find_nodes(modguigui, ns_modgui.thumbnail , None), None)

            if modgui_scrn is not None:
                gui['screenshot'] = modgui_scrn.get_path()
                if not os.path.exists(gui['screenshot']):
                    errors.append("modgui screenshot file is missing")
                if not useAbsolutePath:
                    gui['screenshot'] = gui['screenshot'].replace(bundle,"",1)
            else:
                errors.append("modgui has no screnshot data")

            if modgui_thumb is not None:
                gui['thumbnail'] = modgui_thumb.get_path()
                if not os.path.exists(gui['thumbnail']):
                    errors.append("modgui thumbnail file is missing")
                if not useAbsolutePath:
                    gui['thumbnail'] = gui['thumbnail'].replace(bundle,"",1)
            else:
                errors.append("modgui has no thumbnail data")

            # extra stuff, all optional
            modgui_brand = first_or(world.find_nodes(modguigui, ns_modgui.brand, None), None)
            modgui_label = first_or(world.find_nodes(modguigui, ns_modgui.label, None), None)
            modgui_model = first_or(world.find_nodes(modguigui, ns_modgui.model, None), None)
            modgui_panel = first_or(world.find_nodes(modguigui, ns_modgui.panel, None), None)
            modgui_color = first_or(world.find_nodes(modguigui, ns_modgui.color, None), None)
            modgui_knob = first_or(world.find_nodes(modguigui, ns_modgui.knob , None), None)

            if modgui_brand is not None:
                gui['brand'] = str(modgui_brand)
            if modgui_label is not None:
                gui['label'] = str(modgui_label)
            if modgui_model is not None:
                gui['model'] = str(modgui_model)
            if modgui_panel is not None:
                gui['panel'] = str(modgui_panel)
            if modgui_color is not None:
                gui['color'] = str(modgui_color)
            if modgui_knob is not None:
                gui['knob'] = str(modgui_knob)

            # ports
            errpr = False
            sybls = []
            ports = []
            for port in world.find_nodes(modguigui, ns_modgui.port, None):
                port_indx = first_or(world.find_nodes(port, ns_lv2core.index, None), None)
                port_symb = first_or(world.find_nodes(port, ns_lv2core.symbol, None), None)
                port_name = first_or(world.find_nodes(port, ns_lv2core.name, None), None)

                if None in (port_indx, port_name, port_symb):
                    if not errpr:
                        errors.append("modgui has some invalid port data")
                        errpr = True
                    continue

                port_indx = int(port_indx)
                port_symb = str(port_symb)
                port_name = str(port_name)

                ports.append({
                    'index' : port_indx,
                    'symbol': port_symb,
                    'name'  : port_name,
                })

                if port_symb not in sybls:
                    sybls.append(port_symb)
                elif not errpr:
                    errors.append("modgui has some duplicated port symbols")
                    errpr = True

            # sort ports
            if len(ports) > 0:
                ports2 = {}

                for port in ports:
                    ports2[port['index']] = port
                gui['ports'] = [ports2[i] for i in ports2]

    # --------------------------------------------------------------------------------------------------------
    # ports

    index = 0
    ports = {
        'audio'  : { 'input': [], 'output': [] },
        'control': { 'input': [], 'output': [] },
        'midi'   : { 'input': [], 'output': [] }
    }

    portsymbols = []
    portnames   = []

    # function for filling port info
    def fill_port_info(port):
        # base data
        portname = str_or(port.get_name())

        if not portname:
            portname = "_%i" % index
            errors.append("port with index %i has no name" % index)

        portsymbol = str_or(port.get_symbol())

        if not portsymbol:
            portsymbol = "_%i" % index
            errors.append("port with index %i has no symbol" % index)

        # check for duplicate names
        if portname in portnames:
            warnings.append("port name '%s' is not unique" % portname)
        else:
            portnames.append(portname)

        # check for duplicate symbols
        if portsymbol in portsymbols:
            errors.append("port symbol '%s' is not unique" % portsymbol)
        else:
            portsymbols.append(portsymbol)

        # short name
        psname = str_first_or(port.get_value(ns_lv2core.shortName))

        if not psname:
            psname = get_short_port_name(portname)
            if len(psname) > 16:
                warnings.append("port '%s' name is too big, reduce the name size or provide a shortName" % portname)

        elif len(psname) > 16:
            psname = psname[:16]
            errors.append("port '%s' short name has more than 16 characters" % portname)

        # check for old style shortName
        if first_or(port.get_value(ns_lv2core.shortname), None) is not None:
            errors.append("port '%s' short name is using old style 'shortname' instead of 'shortName'" % portname)

        # port types
        types = [typ.rsplit("#",1)[-1].replace("Port","",1) for typ in get_port_data(port, ns_rdf.type_)]

        if "Atom" in types \
            and port.supports_event(ns_midi.MidiEvent) \
            and str_first_or(port.get_value(ns_atom.bufferType)) == ns_atom.Sequence:
                types.append("MIDI")

        #if "Morph" in types:
            #morphtyp = str_first_or(port.get_value(ns_morph.supportsType))
            #if morphtyp:
                #types.append(morphtyp.rsplit("#",1)[-1].replace("Port","",1))

        # port comment
        pcomment = (get_port_data(port, ns_rdfs.comment) or [""])[0]

        # port designation
        designation = (get_port_data(port, ns_lv2core.designation) or [""])[0]

        # port rangeSteps
        rangeSteps = (get_port_data(port, ns_mod.rangeSteps) or get_port_data(port, ns_pprops.rangeSteps) or [None])[0]

        # port properties
        properties = [typ.rsplit("#",1)[-1] for typ in get_port_data(port, ns_lv2core.portProperty)]

        # data
        ranges      = {}
        scalepoints = []

        # unit block
        ulabel  = ""
        urender = ""
        usymbol = ""

        # control and cv must contain ranges, might contain scale points
        if "Control" in types or "CV" in types:
            isInteger = "integer" in properties

            if isInteger and "CV" in types:
                errors.append("port '%s' has integer property and CV type" % portname)

            xdefault = first_or(port.get_value(ns_mod.default), first_or(port.get_value(ns_lv2core.default), None))
            xminimum = first_or(port.get_value(ns_mod.minimum), first_or(port.get_value(ns_lv2core.minimum), None))
            xmaximum = first_or(port.get_value(ns_mod.maximum), first_or(port.get_value(ns_lv2core.maximum), None))

            if xminimum is not None and xmaximum is not None:
                if isInteger:
                    if xminimum.is_int():
                        ranges['minimum'] = int(xminimum)
                    elif xminimum.is_float():
                        ranges['minimum'] = int(float(xminimum))
                        warnings.append("port '%s' has integer property but minimum value is not an integer" % portname)
                    else:
                        errors.append("port '%s' minimum value is not an integer or float" % portname)

                    if xmaximum.is_int():
                        ranges['maximum'] = int(xmaximum)
                    elif xmaximum.is_float():
                        ranges['maximum'] = int(float(xmaximum))
                        warnings.append("port '%s' has integer property but maximum value is not an integer" % portname)
                    else:
                        errors.append("port '%s' maximum value is not an integer or float" % portname)

                else:
                    if xminimum.is_float():
                        ranges['minimum'] = float(xminimum)
                    elif xminimum.is_int():
                        ranges['minimum'] = float(int(xminimum))
                        warnings.append("port '%s' does not have integer property but minimum value is an integer" % portname)
                    else:
                        ranges['minimum'] = 0.0
                        errors.append("port '%s' minimum value is not an integer or float" % portname)

                    if xmaximum.is_float():
                        ranges['maximum'] = float(xmaximum)
                    elif xmaximum.is_int():
                        ranges['maximum'] = float(int(xmaximum))
                        warnings.append("port '%s' does not have integer property but maximum value is an integer" % portname)
                    else:
                        ranges['maximum'] = 1.0
                        errors.append("port '%s' maximum value is not an integer or float" % portname)

                if ranges['minimum'] >= ranges['maximum']:
                    ranges['maximum'] = ranges['minimum'] + (1 if isInteger else 0.1)
                    errors.append("port '%s' minimum value is equal or higher than its maximum" % portname)

                if xdefault is not None:
                    if isInteger:
                        if xdefault.is_int():
                            ranges['default'] = int(xdefault)
                        elif xdefault.is_float():
                            ranges['default'] = int(float(xdefault))
                            warnings.append("port '%s' has integer property but default value is not an integer" % portname)
                        else:
                            ranges['default'] = ranges['minimum']
                            errors.append("port '%s' default value is not an integer or float" % portname)

                    else:
                        if xdefault.is_float():
                            ranges['default'] = float(xdefault)
                        elif xdefault.is_int():
                            ranges['default'] = float(int(xdefault))
                            warnings.append("port '%s' does not have integer property but default value is an integer" % portname)
                        else:
                            ranges['default'] = 0.0
                            errors.append("port '%s' default value is not an integer or float" % portname)

                    testmin = ranges['minimum']
                    testmax = ranges['maximum']

                    if "sampleRate" in properties:
                        testmin *= 48000
                        testmax *= 48000

                    if not (testmin <= ranges['default'] <= testmax):
                        ranges['default'] = ranges['minimum']
                        errors.append("port '%s' default value is out of bounds" % portname)

                else:
                    ranges['default'] = ranges['minimum']

                    if "Input" in types:
                        errors.append("port '%s' is missing default value" % portname)

            else:
                if isInteger:
                    ranges['minimum'] = 0
                    ranges['maximum'] = 1
                    ranges['default'] = 0
                else:
                    ranges['minimum'] = -1.0 if "CV" in types else 0.0
                    ranges['maximum'] = 1.0
                    ranges['default'] = 0.0

                if "CV" not in types and designation != (PREFIX_LV2CORE + "latency"):
                    errors.append("port '%s' is missing value ranges" % portname)

            scalepoint_nodes = port.get_scale_points()

            if scalepoint_nodes is not None:
                scalepoints_unsorted = []

                for sp in scalepoint_nodes:
                    label = sp.get_label()
                    value = sp.get_value()

                    if label is None:
                        errors.append("a port scalepoint is missing its label")
                        continue

                    label = str(label)

                    if not label:
                        errors.append("a port scalepoint label is empty")
                        continue

                    if value is None:
                        errors.append("port scalepoint '%s' is missing its value" % label)
                        continue

                    if isInteger:
                        if value.is_int():
                            value = int(value)
                        elif value.is_float():
                            value = float(value)
                            warnings.append("port '%s' scalepoint '%s' value is not an integer" % (portname, label))
                        else:
                            value = ranges['minimum']
                            warnings.append("port '%s' scalepoint '%s' value is not an integer or float" % (portname, label))

                    else:
                        if value.is_int():
                            value = int(value)
                            warnings.append("port '%s' scalepoint '%s' value is an integer" % (portname, label))
                        elif value.is_float():
                            value = float(value)
                        else:
                            value = ranges['minimum']
                            warnings.append("port '%s' scalepoint '%s' value is not an integer or float" % (portname, label))

                    if ranges['minimum'] <= value <= ranges['maximum']:
                        scalepoints_unsorted.append((value, label))
                    else:
                        errors.append(("port scalepoint '%s' has an out-of-bounds value:\n" % label) +
                                      ("%d < %d < %d" if isInteger else "%f < %f < %f") % (ranges['minimum'], value, ranges['maximum']))

                if len(scalepoints_unsorted) != 0:
                    unsorted = dict(s for s in scalepoints_unsorted)
                    values   = list(v for v, l in scalepoints_unsorted)
                    values.sort()
                    scalepoints = list({ 'value': v, 'label': unsorted[v] } for v in values)

            if "enumeration" in properties and len(scalepoints) <= 1:
                errors.append("port '%s' wants to use enumeration but doesn't have enough values" % portname)
                properties.remove("enumeration")

        # control ports might contain unit
        if "Control" in types:
            # unit
            uunit = first_or(port.get_value(ns_units.unit), None)

            if uunit is not None:
                uuri = str(uunit)

                # using pre-existing lv2 unit
                if uuri is not None and uuri.startswith("http://lv2plug.in/ns/"):
                    uuri  = uuri.replace("http://lv2plug.in/ns/extensions/units#","",1)
                    uuri  = uuri.replace(PREFIX_MOD,"",1)
                    alnum = uuri.isalnum()

                    if not alnum:
                        errors.append("port '%s' has wrong lv2 unit uri" % portname)
                        uuri = uuri.rsplit("#",1)[-1].rsplit("/",1)[-1]

                    ulabel, urender, usymbol = get_port_unit(uuri)

                    if alnum and not (ulabel and urender and usymbol):
                        errors.append("port '%s' has unknown lv2 unit (our bug?, data is '%s', '%s', '%s')" % (portname,
                                                                                                               ulabel,
                                                                                                               urender,
                                                                                                               usymbol))

                # using custom unit
                else:
                    xlabel = first_or(world.find_nodes(uunit, ns_rdfs.label, None), None)
                    xrender = first_or(world.find_nodes(uunit, ns_units.render, None), None)
                    xsymbol = first_or(world.find_nodes(uunit, ns_units.symbol, None), None)

                    if xlabel is not None:
                        ulabel = str(xlabel)
                    else:
                        errors.append("port '%s' has custom unit with no label" % portname)

                    if xrender is not None:
                        urender = str(xrender)
                    else:
                        errors.append("port '%s' has custom unit with no render" % portname)

                    if xsymbol is not None:
                        usymbol = str(xsymbol)
                    else:
                        errors.append("port '%s' has custom unit with no symbol" % portname)

        return (types, {
            'name'   : portname,
            'symbol' : portsymbol,
            'ranges' : ranges,
            'units'  : {
                'label' : ulabel,
                'render': urender,
                'symbol': usymbol,
            } if "Control" in types and ulabel and urender and usymbol else {},
            'comment'    : pcomment,
            'designation': designation,
            'properties' : sorted(properties),
            'rangeSteps' : rangeSteps,
            'scalePoints': scalepoints,
            'shortName'  : psname,
        })

    for p in (plugin.get_port_by_index(i) for i in range(plugin.get_num_ports())):
        types, info = fill_port_info(p)

        info['index'] = index
        index += 1

        isInput = "Input" in types
        types.remove("Input" if isInput else "Output")

        for typ in [typl.lower() for typl in types]:
            if typ not in ports.keys():
                ports[typ] = { 'input': [], 'output': [] }
            ports[typ]["input" if isInput else "output"].append(info)

    # --------------------------------------------------------------------------------------------------------
    # presets

    def get_preset_data(preset):
        world.load_resource(preset)

        uri   = str_or(preset)
        label = str_first_or(world.find_nodes(preset, ns_rdfs.label, None))

        if not uri:
            errors.append("preset with label '%s' has no uri" % (label or "<unknown>"))
        if not label:
            errors.append("preset with uri '%s' has no label" % (uri or "<unknown>"))

        return (uri, label)

    presets = []

    presets_data = tuple(get_preset_data(p) for p in plugin.get_related(ns_pset.Preset))

    if len(presets_data) != 0:
        unsorted = dict(p for p in presets_data)
        uris     = list(unsorted.keys())
        uris.sort()
        presets  = list({ 'uri': p, 'label': unsorted[p] } for p in uris)
        del unsorted, uris

    # --------------------------------------------------------------------------------------------------------
    # done

    return {
        'uri' : uri,
        'name': name,

        'binary' : binary,
        'brand'  : brand,
        'label'  : label,
        'license': license,
        'comment': comment,

        'category'    : get_category(plugin.get_value(ns_rdf.type_)),
        'microVersion': microVersion,
        'minorVersion': minorVersion,

        'version'  : version,
        'stability': stability,

        'author' : author,
        'bundles': sorted(bundles),
        'gui'    : gui,
        'ports'  : ports,
        'presets': presets,

        'errors'  : sorted(errors),
        'warnings': sorted(warnings),
    }

# ------------------------------------------------------------------------------------------------------------
# get_plugin_info_helper

# Get info from a simple URI, without the need of your own lilv world
# This is used by get_plugins_info in MOD-SDK
def get_plugin_info_helper(uri):
    world = lilv.World()
    world.load_all()
    plugins = world.get_all_plugins()
    return [get_plugin_info(world, p, False) for p in plugins]

# ------------------------------------------------------------------------------------------------------------
# get_plugins_info

# Get plugin-related info from a list of lv2 bundles
# @a bundles is a list of strings, consisting of directories in the filesystem (absolute pathnames).
def get_plugins_info(bundles):
    # if empty, do nothing
    if len(bundles) == 0:
        raise Exception('get_plugins_info() - no bundles provided')

    # Create our own unique lilv world
    # We'll load the selected bundles and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    world.load_specifications()
    world.load_plugin_classes()

    # load all bundles
    for bundle in bundles:
        # lilv wants the last character as the separator
        bundle = os.path.abspath(bundle)
        if not bundle.endswith(os.sep):
            bundle += os.sep

        # convert bundle string into a lilv node
        bundlenode = world.new_file_uri(None, bundle)

        # load the bundle
        world.load_bundle(bundlenode)

    # get all plugins available in the selected bundles
    plugins = world.get_all_plugins()

    # make sure the bundles include something
    if len(plugins) == 0:
        raise Exception('get_plugins_info() - selected bundles have no plugins')

    # return all the info
    return [get_plugin_info(world, p, False) for p in plugins]

# ------------------------------------------------------------------------------------------------------------

def main():
    from sys import argv
    from pprint import pprint

    for i in get_plugins_info(argv[1:]):
        warnings = i['warnings'].copy()

        if 'plugin brand is missing' in warnings:
            i['warnings'].remove('plugin brand is missing')

        if 'plugin label is missing' in warnings:
            i['warnings'].remove('plugin label is missing')

        if 'no modgui available' in warnings:
            i['warnings'].remove('no modgui available')

        for warn in warnings:
            if "has no short name" in warn:
                i['warnings'].remove(warn)

        pprint({
            'uri'     : i['uri'],
            'errors'  : i['errors'],
            'warnings': i['warnings']
        }, width=200)

# ------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

# ------------------------------------------------------------------------------------------------------------
