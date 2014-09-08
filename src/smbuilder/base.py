import includescanner
import util

import fileinput
import fnmatch
import glob
import os
import shutil
import subprocess


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
    def __init__(self, name, plugins, filegroups, extends_list, cfg, configs,
                 translations, data, gamedata, smbuildfile, template_files, template_args, warn_undefined_args):
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
        self.warn_undefined_args = warn_undefined_args

    def create(self, output_dir, filelist, packages, plugins):
        # clears out the package, then rebuilds it
        package_dir = os.path.join(output_dir, self.name)
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        util.mkdir(package_dir)
        build_package(self, package_dir, packages, plugins)
        replace_args(self, package_dir, packages)

        # create package description filegroups
        if filelist:
            list = util.list_files_recursively(package_dir)
            with open(os.path.join(package_dir, 'files.txt'), 'w') as f:
                for package_file in list:
                    f.write(package_file + '\n')


def build_package(package, package_dir, packages=None, plugins=None):
    for p in package.extends_list:
        try:
            build_package(packages[p], package_dir, packages, plugins)
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

    util.safe_copytree(package.configs, config_dir)
    util.safe_copytree(package.translations, translation_dir)
    util.safe_copytree(package.cfg, cfg_dir)
    util.safe_copytree(package.data, data_dir)
    util.safe_copytree(package.gamedata, gamedata_dir)


def replace_args(package, package_dir, packages):
    template_args = get_template_args(package, packages)

    for root, dirs, files in os.walk(package_dir):
        for file in files:
            path = os.path.join(root, file)
            if '.smx' not in path:
                filedata = ''
                with open(path, 'r') as f:
                    filedata = f.read()
                filedata = templatize(filedata, template_args)
                if package.warn_undefined_args:
                    check_undefined_templates(filedata, package, file)
                with open(path, 'w') as f:
                    f.write(filedata)


def templatize(text, args):
    used_args = set()
    for key in args:
        value = str(args[key])
        new_text = text.replace('%' + key + '%', value)
        new_text = new_text.replace('$' + key + '$', key + ' ' + value)
        if text != new_text:
            used_args.add(key)
        text = new_text
    return text


def get_template_args(package, packages):
    args = {}
    # get inherited values
    for base_name in package.extends_list:
        base = packages[base_name]
        args.update(get_template_args(base, packages))

    # get values from this package, overwriting old ones
    for arg in package.template_args:
        args[arg] = package.template_args[arg]
    return args


def check_undefined_templates(text, package, filename):
    for word in text.split():
        first = word[0]
        last = word[-1]
        if len(word) >= 3 and first == last and (first == '$' or first == '%'):
            msg = 'Undefined template argument: \'{}\': from package \'{}\', file \'{}\''.format(word, package.name, filename)
            util.warning(msg)
