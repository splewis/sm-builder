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

    Plugins[name] = PluginContainer(name, source_path, compiler, current_path)


class PluginContainer:
    def __init__(self, name, source, compiler, config_source):
        self.name = name
        self.source = os.path.abspath(source)
        self.compiler = compiler
        self.config_source = self.config_source

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


def register_package(name=None, plugins=None, plugin_out='addons/sourcemod/plugins', filegroups=None, extends=None):
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
    else:
        filegroups = {}

    if not plugins:
        plugins = []

    if not extends:
        extends = []

    Packages[name] = PackageContainer(name, plugins, plugin_out, filegroups, extends)


class PackageContainer:
    def __init__(self, name, plugins, plugin_out, filegroups, extends_list):
        self.name = name
        self.plugins = plugins
        self.plugin_out = plugin_out
        self.filegroups = filegroups
        self.extends_list = extends_list

    def create(self, output_dir):
        global Plugins

        for base_name in self.extends_list:
            try:
                base = Packages[base_name]
            except KeyError:
                util.error('Package {} extends non-existent package {}'.format(self.name, base_name))

            self.plugins += base.plugins
            for path, files in base.filegroups.iteritems():
                if path not in self.filegroups:
                    self.filegroups[path] = []
                for f in files:
                    # don't allow a base package to overwrite, use the 'lower' file
                    if not f in self.filegroups[path]:
                        self.filegroups[path].append(f)

        package_dir = os.path.join(output_dir, self.name)
        # clears out the package
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        util.mkdir(package_dir)

        plugin_dir = os.path.join(package_dir, self.plugin_out)

        source_dir = os.path.join(plugin_dir, '..', 'scripting')
        source_dir = os.path.abspath(source_dir)
        util.mkdir(source_dir)

        for p in self.plugins:
            if p not in Plugins:
                util.error('Package {} used non-existent plugin {}'.format(self.name, p))

            util.mkdir(plugin_dir)
            binary_path = os.path.join(OUTPUT_DIR, 'plugins', p + '.smx')
            shutil.copy2(binary_path, plugin_dir)
            # TODO: a serious problem is that included files are not also copied over
            shutil.copy2(Plugins[p].source, source_dir)

        for filegroup in self.filegroups:
            filegroup_out_dir = os.path.join(package_dir, filegroup)
            util.mkdir(filegroup_out_dir)
            for f in self.filegroups[filegroup]:
                shutil.copy2(f, filegroup_out_dir)


def main():
    parser = argparse.ArgumentParser(description='smbuild is a build and packaging tool for managing sourcemod plugins and servers')
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
    global DirectoryStack, Plugins

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
        package.create(OUTPUT_DIR)

    if len(Plugins) == 0:
        util.warning('No plugins were found in {}.'.format(os.path.join(config, CONFIG_NAME)))
    elif compiled_count == 0:
        print('All plugins up to date.')


if __name__ == '__main__':
    main()
