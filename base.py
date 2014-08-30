import includescanner
import util

import os
import subprocess
import shutil


class PluginContainer:
    """Wrapper that represents a single sourcemod plugin."""
    def __init__(self, name, source, compiler, smbuildfile, deps):
        self.name = name
        self.source = source
        self.compiler = compiler
        self.smbuildfile = smbuildfile
        self.deps = deps
        self.source_dir = os.path.relpath(os.path.dirname(source), '.')
        self.source_files = set()

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


class PackageContainer:
    """Wrapper that represents a package: a collection of plugins and files."""
    def __init__(self, name, plugins, filegroups, extends_list, cfgs, configs,
                 translations, data, gamedata, smbuildfile):
        self.name = name
        self.plugins = plugins
        self.filegroups = filegroups
        self.extends_list = extends_list
        self.cfgs = cfgs
        self.configs = configs
        self.translations = translations
        self.data = data
        self.gamedata = gamedata
        self.smbuildfile = smbuildfile

    def create(self, output_dir, plugins, packages):
        # clears out the package, then rebuilds it
        package_dir = os.path.join(output_dir, self.name)
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        util.mkdir(package_dir)
        build_package(self, package_dir, packages, plugins)


def build_package(package, package_dir, plugins, packages):
    for p in package.extends_list:
        try:
            build_package(packages[p], package_dir, plugins, packages)
        except KeyError:
            err_msg = 'Package {} extends non-existent package {}'
            util.error(err_msg.format(package.name, p))

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
        if p not in plugins:
            err_msg = 'Package {} used non-existent plugin {}'
            util.error(err_msg.format(package.name, p))

        util.mkdir(plugin_dir)
        binary_path = os.path.join('builds', 'plugins', p + '.smx')
        shutil.copy2(binary_path, plugin_dir)
        for source_file in plugins[p].source_files:
            source_path = os.path.join(plugins[p].source_dir, source_file)
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

    util.copy_package_files(package.configs, config_dir)
    util.copy_package_files(package.translations, translation_dir)
    util.copy_package_files(package.cfgs, cfg_dir)
    util.copy_package_files(package.data, data_dir)
    util.copy_package_files(package.gamedata, gamedata_dir)
