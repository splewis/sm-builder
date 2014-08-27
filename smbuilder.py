#!/usr/bin/env python

import includescanner
import util

import argparse
import os
import glob
import shutil
import subprocess


# Stack of directories entered when reading configs
# Starts at the first directory (current directory or what is passed to -cfg)
# At each Include() statement, that path is added to the stack.
DirectoryStack = []

# Global dicts registered components.
Plugins = {}
Packages = {}

OUTPUT_DIR = 'builds'
CONFIG_NAME = 'smbuild'


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
    global DirectoryStack, InsideInclude
    DirectoryStack.append(path)
    execute_config(os.path.join(*DirectoryStack))
    DirectoryStack.pop()


def register_plugin(name=None, source=None, compiler=None):
    if not source:
        util.error('Plugins must specify a source')
    if not name:
        name = os.path.basename(source)  # get file name from the full path
        name = os.path.splitext(name)[0]  # remove the file extension
    if name in Plugins:
        util.error('duplicated plugin name {}'.format(name))

    current_path = os.path.join(*DirectoryStack)
    source_path = os.path.join(current_path, source)

    Plugins[name] = PluginContainer(name, source_path, compiler, current_path)


class PluginContainer:

    def __init__(self, name, source, compiler, config_source):
        self.name = name
        self.source = source
        self.compiler = compiler
        self.config_source = config_source
        self.source_dir = os.path.relpath(os.path.dirname(source), '.')
        self.source_files = set()
        self.smbuildfile = os.path.join(
            os.path.join(*DirectoryStack), CONFIG_NAME)

    def compile(self, compiler, output_dir):
        latest_source_change, self.source_files = (
            includescanner.find_last_time_modified(self.source))

        if self.compiler:
            compiler_to_use = self.compiler  # uses the plugin-defined compiler
        else:
            compiler_to_use = compiler  # uses the globally-defined compiler

        binary_file_name = os.path.join(output_dir, self.name + '.smx')
        latest_binary_change = 0
        if os.path.exists(binary_file_name):
            latest_binary_change = os.path.getmtime(binary_file_name)

        if latest_source_change > latest_binary_change:
            cmd = '{0} {1} -o={2}'.format(compiler_to_use,
                                          self.source,
                                          os.path.join(output_dir, self.name))
            try:
                print(cmd)
                subprocess.check_call(
                    cmd, shell=True, stderr=subprocess.STDOUT)
                return True
            except subprocess.CalledProcessError:
                err_msg = 'Failed to compile {}, from {}'
                util.error(err_msg.format(self.name, self.smbuildfile))
        else:
            return False


def register_package(name=None, plugins=None, filegroups=None, cfgs=['cfg'],
                     extends=None, configs=['configs'], gamedata=['gamedata'],
                     translations=['translations'], data=['data']):
    if not name:
        util.error('Packages must specify a name')
    if name in Packages:
        util.error('duplicated package name {}'.format(name))
    if name == 'plugins':
        util.error('Illegal package name: {}'.format(name))

    if filegroups:
        for dir in filegroups:
            filegroups[dir] = glob_files(filegroups[dir], name)
    else:
        filegroups = {}

    if not plugins:
        plugins = []
    if not extends:
        extends = []

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

    Packages[name] = PackageContainer(
        name, plugins, filegroups, extends, cfgs, configs, translations, data, gamedata)


def glob_files(file_list, name):
    output = []
    current_path = os.path.join(*DirectoryStack)
    for pattern in file_list:
        matches = glob.glob(os.path.join(current_path, pattern))
        if matches:
            for f in matches:
                output.append(f)

    return output


class PackageContainer:

    def __init__(self, name, plugins, filegroups, extends_list, cfgs, configs,
                 translations, data, gamedata):
        self.name = name
        self.plugins = plugins
        self.filegroups = filegroups
        self.extends_list = extends_list
        self.cfgs = cfgs
        self.configs = configs
        self.translations = translations
        self.data = data
        self.gamedata = gamedata
        self.smbuildfile = os.path.relpath(os.path.join(*DirectoryStack))

    def create(self, output_dir):
        global Plugins

        # clears out the package
        package_dir = os.path.join(OUTPUT_DIR, self.name)
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        util.mkdir(package_dir)
        build_package(self, self.name)


def build_package(package, name):
    for p in package.extends_list:
        try:
            build_package(Packages[p], name)
        except KeyError:
            err_msg = 'Package {} extends non-existent package {}'
            util.error(err_msg.format(package.name, p))

    package_dir = os.path.join(OUTPUT_DIR, name)

    cfg_dir = os.path.join(package_dir, 'cfg')
    sm_dir = os.path.join(package_dir, 'addons', 'sourcemod')
    plugin_dir = os.path.join(sm_dir, 'plugins')
    config_dir = os.path.join(sm_dir, 'configs')
    translation_dir = os.path.join(sm_dir, 'translations')
    data_dir = os.path.join(sm_dir, 'data')
    gamedata_dir = os.path.join(sm_dir, 'gamedata')

    output_source_dir = os.path.join(plugin_dir, '..', 'scripting')
    util.mkdir(output_source_dir)

    for p in package.plugins:
        if p not in Plugins:
            err_msg = 'Package {} used non-existent plugin {}'
            util.error(err_msg.format(package.name, p))

        util.mkdir(plugin_dir)
        binary_path = os.path.join(OUTPUT_DIR, 'plugins', p + '.smx')
        shutil.copy2(binary_path, plugin_dir)
        for source_file in Plugins[p].source_files:
            source_path = os.path.join(Plugins[p].source_dir, source_file)
            output_file_path = os.path.join(output_source_dir, source_file)
            util.mkdir(os.path.dirname(output_file_path))
            shutil.copyfile(source_path, output_file_path)

    for filegroup in package.filegroups:
        filegroup_out_dir = os.path.join(package_dir, filegroup)
        util.mkdir(filegroup_out_dir)
        for f in package.filegroups[filegroup]:
            if os.path.isdir(f):
                util.error(
                    'Only files may be put in filegroups: {}'.format(f))
            shutil.copy2(f, filegroup_out_dir)

    copy_package_files(package.configs, config_dir)
    copy_package_files(package.translations, translation_dir)
    copy_package_files(package.cfgs, cfg_dir)
    copy_package_files(package.data, data_dir)
    copy_package_files(package.gamedata, gamedata_dir)


def copy_package_files(list, dir):
    for f in list:
        if os.path.isdir(f):
            util.copytree(f, dir)
        else:
            shutil.copy2(f, dir)


def main():
    parser = argparse.ArgumentParser(
        description='A sourcemod build and packaging tool.')
    parser.add_argument('target', nargs='?')
    parser.add_argument('-c', '--compiler', default='spcomp',
                        help='Sourcepawn compiler to use.')
    args = parser.parse_args()

    # default to building all targets in current directory
    if not args.target:
        args.target =':all'

    perform_builds(args.target, args.compiler)


def clean():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)


def perform_builds(target, compiler):
    global DirectoryStack, Plugins

    if target == 'clean':
        clean()
        return

    plugin_build_dir = os.path.join(OUTPUT_DIR, 'plugins')

    try:
        config_dir = target[:target.index(':')]
        if config_dir == '':
            config_dir = '.'
        target_name = target[target.index(':')+1:]
    except ValueError:
        util.error('Got bad target name: {}'.format(target))

    # setup directory structure, execute user-configurations
    util.mkdir(OUTPUT_DIR)
    util.mkdir(plugin_build_dir)
    DirectoryStack = [config_dir]
    execute_config(config_dir)

    # scan deps for what we need to do
    packages_to_build = set()
    for name, package in Packages.iteritems():
        from_this_config = (config_dir == package.smbuildfile)
        if name == target_name or (target_name == 'all' and from_this_config):
            packages_to_build.add(name)

    plugins_to_compile = set()
    for name in packages_to_build:
        for dep in util.find_plugins(Packages[name], Packages):
            plugins_to_compile.add(dep)

    # compile plugins
    compiled_count = 0
    for name in plugins_to_compile:
        plugin = Plugins[name]
        if plugin.compile(compiler, plugin_build_dir):
            compiled_count += 1

    # build packages
    for name in packages_to_build:
        package = Packages[name]
        from_this_config = (config_dir == package.smbuildfile)
        if name == target_name or (target_name == 'all' and from_this_config):
            print('Building package {}'.format(name))
            package.create(OUTPUT_DIR)

    if len(Plugins) == 0:
        util.warning('No plugins were found in {}.'.format(
            os.path.join(config_dir, CONFIG_NAME)))
    elif compiled_count == 0:
        print('All plugins up to date.')


if __name__ == '__main__':
    main()
