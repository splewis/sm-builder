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

OUTPUT_DIR = 'smbuilds'
CONFIG_NAME = 'smbuild'


def glob_plugins(pattern):
    path = os.path.join(*DirectoryStack)
    results = glob.glob(os.path.join(path, pattern))
    for source_file in results:
        register_plugin(source=os.path.abspath(source_file))


def execute_config(dir_path):
    f = os.path.abspath(os.path.join(dir_path, CONFIG_NAME))
    if os.path.exists(f):
        context = {
            'Include': register_include,
            'Plugin': register_plugin,
            'Package': register_package,
            'GlobPlugins': glob_plugins,
        }
        execfile(f, context)
    else:
        util.error('Config file does not exist: {}'.format(f))


def register_include(path):
    global DirectoryStack
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

    Plugins[name] = PluginContainer(name, source_path, compiler)


class PluginContainer:
    def __init__(self, name, source, compiler):
        self.name = name
        self.source = os.path.abspath(source)
        self.compiler = compiler

    def compile(self, compiler, output_dir):
        latest_source_change = includescanner.find_last_time_modified(self.source)

        if self.compiler:
            compiler_to_use = self.compiler  # uses the plugin-defined compiler
        else:
            compiler_to_use = compiler  # uses the globally-defined compiler

        binary_file_name = os.path.join(output_dir, self.name + '.smx')
        latest_binary_change = 0
        if os.path.exists(binary_file_name):
            latest_binary_change = os.path.getmtime(binary_file_name)

        if latest_source_change > latest_binary_change:
            cmd = '{0} {1} -o={2}'.format(compiler_to_use, self.source, os.path.join(output_dir, self.name))
            try:
                subprocess.check_call(cmd, shell=True)
                return True
            except subprocess.CalledProcessError:
                util.error('Failed to compile {}'.format(self.name))
        else:
            return False


def register_package(name=None, plugins=None, plugin_out='addons/sourcemod/plugins', filegroups=None):
    if not name:
        util.error('Packages must specify a name')
    if name in Packages:
        util.error('duplicated package name {}'.format(name))
    if name == 'plugins':
        util.error('Illegal package name: {}'.format(name))

    if filegroups:
        for dir in filegroups:
            current_path = os.path.join(*DirectoryStack)
            filegroups[dir] = map(lambda f: os.path.abspath(os.path.join(current_path, f)), filegroups[dir])

    Packages[name] = PackageContainer(name, plugins, plugin_out, filegroups)


class PackageContainer:
    def __init__(self, name, plugins, plugin_out, filegroups):
        self.name = name
        self.plugins = plugins
        self.plugin_out = plugin_out
        self.filegroups = filegroups

    def create(self, output_dir):
        print 'Building package {}.'.format(self.name)
        package_dir = os.path.join(output_dir, self.name)
        plugin_dir = os.path.join(package_dir, self.plugin_out)

        for p in self.plugins:
            util.mkdir(plugin_dir)
            plugin = Plugins[p]
            binary_path = os.path.join(OUTPUT_DIR, 'plugins', p + '.smx')
            shutil.copy2(binary_path, plugin_dir)

        for filegroup in self.filegroups:
            filegroup_out_dir = os.path.join(package_dir, filegroup)
            util.mkdir(filegroup_out_dir)
            for f in self.filegroups[filegroup]:
                shutil.copy2(f, filegroup_out_dir)


def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('-cfg', '--config', default='.', help='Directory to read a smbuild config file from')
    parser.add_argument('-c', '--compiler', default='spcomp', help='Sourcepawn compiler to use, this is executed directly by a shell')
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()

    if args.clean:
        shutil.rmtree(OUTPUT_DIR)
    else:
        perform_builds(args.config, args.compiler)


def clean():
    shutil.rmtree(OUTPUT_DIR)


def perform_builds(config, compiler):
    global DirectoryStack

    plugin_build_dir = os.path.join(OUTPUT_DIR, 'plugins')

    util.mkdir(OUTPUT_DIR)
    util.mkdir(plugin_build_dir)
    DirectoryStack = [config]
    execute_config(config)

    compiled_count = 0
    for name, plugin in Plugins.iteritems():
        if plugin.compile(compiler, plugin_build_dir):
            compiled_count += 1

    for name, package in Packages.iteritems():
        package.create('OUTPUT_DIR')

    if len(Plugins) == 0:
        util.warning('No plugins were found in {}.'.format(os.path.join(ActiveDirectory, CONFIG_NAME)))
    elif compiled_count == 0:
        print 'All plugins up to date.'


if __name__ == '__main__':
    main()
