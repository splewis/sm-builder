import base
import util

import fnmatch
import glob
import os


CONFIG_NAME = 'smbuild'
IncludedPaths = set()
Packages = {}
Plugins = {}
DirectoryStack = []


def parse_configs(config_dir):
    """
    Exectues a smbuild configuration file in the given directory and
    builds the global data structures needed.
    (i.e. the Plugins and Packages dictionaries)
    """
    global DirectoryStack, Packages, Plugins, IncludedPaths
    IncludedPaths = set()
    Plugins = {}
    Packages = {}
    DirectoryStack = [config_dir]
    execute_config(config_dir)
    check_package_cycles(Packages)
    return Plugins, Packages


def glob_plugins(pattern):
    """
    Registers all source files that match a pattern
    as a Plugin.
    """
    path = os.path.join(*DirectoryStack)
    results = glob.glob(os.path.join(path, pattern))
    for source_file in results:
        register_plugin(source=source_file)


def list_glob_plugins(pattern):
    return list(filter(lambda x: fnmatch.fnmatch(x, pattern), Plugins.keys()))


def execute_config(dir_path):
    """
    Executes an smbuild configuration file.
    """
    filename = os.path.abspath(os.path.join(dir_path, CONFIG_NAME))
    if os.path.exists(filename):
        context = {
            'Include': register_include,
            'Plugin': register_plugin,
            'Package': register_package,
            'GlobPlugins': glob_plugins,
            'Plugins': list_glob_plugins,
        }
        with open(filename) as f:
            exec(f.read(), context)
            try:
                exec(f.read(), context)
            except Exception as e:
                msg = 'There is a syntax error in {}\n{}'.format(filename, e)
                raise SyntaxError(msg)

    else:
        msg = 'Config file does not exist: {}'.format(filename)
        raise IOError(msg)


def register_include(path):
    """
    Registers an include, adding any files from that include
    to the global data structures.
    """
    global DirectoryStack

    if path == 'stocks':
        # TODO: setuptools has a better notion of package data files,
        # so it might be worth looking into using that later.
        dirpath = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dirpath, 'plugins')

    abspath = os.path.abspath(path)
    if abspath not in IncludedPaths:
        DirectoryStack.append(path)
        execute_config(os.path.join(*DirectoryStack))
        DirectoryStack.pop()
        IncludedPaths.add(abspath)


def register_plugin(name=None, source=None, deps=None, binary=None):
    """
    Registers a new Plugin.
    """
    source_path = None
    binary_path = None
    current_path = os.path.join(*DirectoryStack)

    if source and binary:
        msg = 'the source and binary fields cannot be used together in a plugin'
        raise ValueError(msg)
    if source:
        source_path = os.path.join(current_path, source)
        if not name:
            name = util.file_to_plugin_name(source)
    elif binary:
        binary_path = os.path.join(current_path, binary)
        if not name:
            name = util.file_to_plugin_name(binary)
    else:
        msg = 'Plugin {} does not define either a source or a binary'.format(name)
        raise ValueError(msg)

    if name in Plugins:
        msg = 'duplicated plugin name {}'.format(name)
        raise ValueError(msg)

    smbuildfile = os.path.join(current_path, CONFIG_NAME)

    if deps is None:
        deps = []

    Plugins[name] = base.PluginContainer(name, source_path, binary_path, smbuildfile, deps)


def register_package(name=None, plugins=None, disabled_plugins=None, filegroups=None, extends=None,
                     sources=None, template_files=None, args=None,
                     cfg='cfg', configs='configs', gamedata='gamedata',
                     translations='translations', data='data'):
    """
    Registers a new Package.
    The name field is mandatory.
    """
    if not name:
        raise ValueError('Packages must specify a name')
    if name in Packages:
        raise ValueError('duplicated package name {}'.format(name))
    if name == 'plugins':
        raise ValueError('Illegal package name: {}'.format(name))

    if filegroups:
        for dir in filegroups:
            filegroups[dir] = glob_files(filegroups[dir], name, True)
    else:
        filegroups = {}

    if not plugins:
        plugins = []
    if not disabled_plugins:
        disabled_plugins = []
    if not extends:
        extends = []
    if not template_files:
        template_files = []
    if not args:
        args = {}

    if sources:
        for s in sources:
            register_plugin(source=s)
            plugins.append(util.file_to_plugin_name(s))

    current_path = os.path.join(*DirectoryStack)
    smbuildfile = os.path.join(current_path, CONFIG_NAME)

    if cfg:
        cfg = os.path.join(current_path, cfg)
    if translations:
        translations = os.path.join(current_path, translations)
    if gamedata:
        gamedata = os.path.join(current_path, gamedata)
    if configs:
        configs = os.path.join(current_path, configs)
    if data:
        data = os.path.join(current_path, data)

    Packages[name] = base.PackageContainer(
        name, plugins, filegroups, extends, cfg, configs,
        translations, data, gamedata, smbuildfile, template_files, args, disabled_plugins)


def glob_files(file_list, name, warn_on_empty=False):
    """
    Support function for pattern matching on files that
    returns a list of matching files.
    """
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


def check_package_cycles(Packages):
    # TODO: this should cause a util.error is a package cycle is detected
    pass
