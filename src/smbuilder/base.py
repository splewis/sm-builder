from . import includescanner 
from . import util 

import fileinput
import fnmatch
import glob
import os
import shutil
import subprocess

import jinja2


class PluginContainer:
    """Wrapper that represents a single sourcemod plugin."""
    def __init__(self, name, source, binary, smbuildfile, deps):
        self.name = name
        self.source = source
        self.binary = binary
        self.smbuildfile = smbuildfile
        self.deps = deps
        if source:
            self.source_dir = os.path.relpath(os.path.dirname(source), '.')
        else:
            self.source_dir = os.path.relpath(os.path.dirname(binary), '.')

        self.source_files = set()

    def compile(self, compiler, output_dir, flags):
        """Compiles, if needed the plugin and returns whether it was compiled."""
        if self.binary:
            shutil.copyfile(self.binary, os.path.join(output_dir, self.name + '.smx'))
            return False

        latest_source_change, self.source_files = (
            includescanner.find_last_time_modified(self.source))

        binary_file_name = os.path.join(output_dir, self.name + '.smx')
        latest_binary_change = 0
        if os.path.exists(binary_file_name):
            latest_binary_change = os.path.getmtime(binary_file_name)

        error_filename = os.path.join(output_dir, self.name + '.txt')

        def get_error_text():
            error_text = None
            if os.path.exists(error_filename):
                with open(error_filename) as f:
                    error_text = f.read().strip()
            return error_text

        if latest_source_change > latest_binary_change:
            out = os.path.join(output_dir, self.name)
            cmd = '{} {} {} -o={} -e={}'
            cmd = cmd.format(compiler, self.source, flags, out, error_filename)

            try:
                # clear the previous error output file
                if os.path.exists(error_filename):
                    os.remove(error_filename)

                # run the actual command
                print(cmd)
                subprocess.check_call(
                    cmd, shell=True, stderr=subprocess.STDOUT)

                text = get_error_text()
                if text:
                    util.warning(text)

                return True

            except subprocess.CalledProcessError:
                msg = 'Failed to compile {}, from {}\n{}'
                util.error(msg.format(self.name, self.smbuildfile, get_error_text()))

        else:
            text = get_error_text()
            if text:
                util.warning(text)
            return False



class PackageContainer:
    """Wrapper that represents a package: a collection of plugins and files."""
    def __init__(self, name, plugins, filegroups, extends_list, cfg, configs,
                 translations, data, gamedata, smbuildfile, template_files, template_args, disabled):
        self.name = name
        self.plugins = plugins
        self.filegroups = filegroups
        self.extends_list = extends_list
        self.cfg = cfg
        self.configs = configs
        self.translations = translations
        self.data = data
        self.gamedata = gamedata
        self.smbuildfile = smbuildfile
        self.template_files = template_files
        self.template_args = template_args
        self.disabled = disabled

    def create(self, output_dir, packages, plugins, nosource):
        """Creates the package output."""
        # clears out the package, then rebuilds it
        package_dir = os.path.join(output_dir, self.name)
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        util.mkdir(package_dir)
        build_package(self, package_dir, packages, plugins, nosource)
        replace_args(self, package_dir, packages, plugins)

        # deal with any plugins supposed to be disabled
        plugin_dir = os.path.join(package_dir, 'addons', 'sourcemod', 'plugins')
        disabled_dir = os.path.join(package_dir, 'addons', 'sourcemod', 'plugins', 'disabled')
        if self.disabled:
            util.mkdir(disabled_dir)
            for p in self.disabled:
                src = os.path.join(plugin_dir, plugins[p].name + '.smx')
                dst = os.path.join(disabled_dir, plugins[p].name + '.smx')

                if not os.path.exists(src):
                    msg = 'Package {} uses disables plugin {}, which it does not contain'
                    util.error(msg.format(self.name, p))

                shutil.move(src, dst)


def build_package(package, package_dir, packages, plugins, nosource):
    """Support function for building package files into a given directory."""
    for p in package.extends_list:
        try:
            build_package(packages[p], package_dir, packages, plugins, nosource)
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

    for p in package.plugins:
        if p not in plugins:
            err_msg = 'Package {} used non-existent plugin {}'
            util.error(err_msg.format(package.name, p))

        # copy plugin binaries
        util.mkdir(plugin_dir)
        binary_path = os.path.join(package_dir, '..', 'plugins', p + '.smx')
        shutil.copy2(binary_path, plugin_dir)

        # copy source files
        if not nosource:
            util.mkdir(output_source_dir)
            for source_file in plugins[p].source_files:
                source_path = os.path.join(plugins[p].source_dir, source_file)
                output_file_path = os.path.join(output_source_dir, source_file)
                util.mkdir(os.path.dirname(output_file_path))
                shutil.copyfile(source_path, output_file_path)

    # copy filegroup definitions
    for filegroup in package.filegroups:
        filegroup_out_dir = os.path.join(package_dir, filegroup)
        util.mkdir(filegroup_out_dir)
        for f in package.filegroups[filegroup]:
            if os.path.isdir(f):
                util.copytree()
            else:
                shutil.copy2(f, filegroup_out_dir)

    # copy everything else
    util.safe_copytree(package.configs, config_dir)
    util.safe_copytree(package.translations, translation_dir)
    util.safe_copytree(package.cfg, cfg_dir)
    util.safe_copytree(package.data, data_dir)
    util.safe_copytree(package.gamedata, gamedata_dir)


def replace_args(package, package_dir, packages, plugins):
    """Performs replacement of template arguments within a directory for a package."""
    template_args = get_template_args(package, packages, plugins)

    for root, dirs, files in os.walk(package_dir):
        for file in files:
            path = os.path.join(root, file)
            text_extensions = ['.cfg', '.ini', '.txt']
            if any(map(lambda extension: extension in file, text_extensions)):
                filedata = ''
                with open(path, 'r') as f:
                    filedata = f.read()
                    templatized = ''
                    try:
                        templatized = templatize(filedata, template_args)
                    except UnicodeDecodeError:
                        templatized = filedata
                with open(path, 'w') as f:
                    f.write(templatized)


def templatize(text, args):
    """Replaces template arguments in a string of text."""
    template = jinja2.Template(text)
    return template.render(**args)


def get_template_args(package, packages, plugins):
    """Returns a dictionary of all arguments a package contains."""
    args = {}
    # get inherited values
    for base_name in package.extends_list:
        base = packages[base_name]
        args.update(get_template_args(base, packages, plugins))

    # get values from this package, overwriting old ones
    for arg in package.template_args:
        args[arg] = package.template_args[arg]

    # create extra plugin_binaries argument
    plugin_binaries = []
    deps = find_plugin_deps(package, packages)
    for dep in deps:
        plugin_binaries.append(plugins[dep].name + '.smx')
    args['plugin_binaries'] = plugin_binaries
    args['package'] = package.name

    return args


def find_plugin_deps(package, packages_dict):
    """Returns a set of plugin names that a package includes."""
    plugins = set()
    for p in package.plugins:
        plugins.add(p)
    for p in package.extends_list:
        if p not in packages_dict:
            err_msg = 'Package {} extends non-existent package {}'
            util.error(err_msg.format(package.name, p))

        plugins.update(find_plugin_deps(packages_dict[p], packages_dict))
    return plugins
