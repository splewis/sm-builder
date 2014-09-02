import base
import util

import os
import glob


CONFIG_NAME = 'smbuild'
IncludedPaths = set()
Packages = {}
Plugins = {}
DirectoryStack = []


def parse_configs(config_dir):
    global DirectoryStack, Packages, Plugins, IncludedPaths
    IncludedPaths = set()
    Plugins = {}
    Packages = {}
    DirectoryStack = [config_dir]
    execute_config(config_dir)
    return Plugins, Packages


def glob_plugins(pattern):
    path = os.path.join(*DirectoryStack)
    results = glob.glob(os.path.join(path, pattern))
    for source_file in results:
        register_plugin(source=source_file)


def execute_config(dir_path):
    filename = os.path.abspath(os.path.join(dir_path, CONFIG_NAME))
    if os.path.exists(filename):
        context = {
            'Include': register_include,
            'Plugin': register_plugin,
            'Package': register_package,
            'GlobPlugins': glob_plugins,
        }
        with open(filename) as f:
            try:
                exec(f.read(), context)
            except Exception as e:
                util.error(
                    'There is a syntax error in {}\n{}'.format(filename, e))
    else:
        util.error('Config file does not exist: {}'.format(filename))


def register_include(path):
    global DirectoryStack
    abspath = os.path.abspath(path)
    if abspath not in IncludedPaths:
        DirectoryStack.append(path)
        execute_config(os.path.join(*DirectoryStack))
        DirectoryStack.pop()
        IncludedPaths.add(abspath)


def register_plugin(name=None, source=None, compiler=None, deps=None):
    if not source:
        util.error('Plugins must specify a source')
    if not name:
        name = util.file_to_plugin_name(source)
    if name in Plugins:
        util.error('duplicated plugin name {}'.format(name))

    current_path = os.path.join(*DirectoryStack)
    source_path = os.path.join(current_path, source)
    smbuildfile = os.path.join(current_path, CONFIG_NAME)

    if deps is None:
        deps = []

    Plugins[name] = base.PluginContainer(name, source_path, compiler, smbuildfile, deps)


def register_package(name=None, plugins=None, filegroups=None, extends=None,
                     sources=None,
                     cfgs=['cfg'], configs=['configs'], gamedata=['gamedata'],
                     translations=['translations'], data=['data']):
    if not name:
        util.error('Packages must specify a name')
    if name in Packages:
        util.error('duplicated package name {}'.format(name))
    if name == 'plugins':
        util.error('Illegal package name: {}'.format(name))

    if filegroups:
        for dir in filegroups:
            filegroups[dir] = glob_files(filegroups[dir], name, True)
    else:
        filegroups = {}

    if not plugins:
        plugins = []
    if not extends:
        extends = []
    if not sources:
        sources = []
    else:
        for s in sources:
            register_plugin(source=s)
            plugins.append(util.file_to_plugin_name(s))

    if cfgs:
        cfgs = glob_files(cfgs, name)
    else:
        cfgs = []

    if configs:
        configs = glob_files(configs, name)
    else:
        configs = []

    if translations:
        translations = glob_files(translations, name)
    else:
        translations = []

    if gamedata:
        gamedata = glob_files(gamedata, name)
    else:
        gamedata = []

    if data:
        data = glob_files(data, name)
    else:
        data = []

    current_path = os.path.join(*DirectoryStack)
    smbuildfile = os.path.join(current_path, CONFIG_NAME)

    Packages[name] = base.PackageContainer(
        name, plugins, filegroups, extends, cfgs, configs, translations, data, gamedata, smbuildfile)


def glob_files(file_list, name, warn_on_empty=False):
    output = []
    current_path = os.path.join(*DirectoryStack)
    for pattern in file_list:
        matches = glob.glob(os.path.join(current_path, pattern))
        if matches:
            for f in matches:
                output.append(f)
        if not matches and warn_on_empty:
            util.warning('No files matched pattern {}'.format(pattern))

    return output
