import base
import util

import os


OUTPUT_DIR = 'builds'


def build(smbuildfile, compiler, filelist, plugins, packages):
    # setup directory structure, execute user-configurations
    plugin_build_dir = os.path.join(OUTPUT_DIR, 'plugins')
    util.mkdir(OUTPUT_DIR)
    util.mkdir(plugin_build_dir)

    # scan deps for what we need to do
    packages_to_build = set()
    for name, package in packages.iteritems():
        if smbuildfile == package.smbuildfile:
            packages_to_build.add(name)

    plugins_to_compile = set()
    for name in packages_to_build:
        for_this_package = find_plugin_deps(packages[name], packages)
        for plugin_name in for_this_package:
            plugins_to_compile.add(plugin_name)

            # also make sure plugin dependencies are met by the package
            for dep in plugins[plugin_name].deps:
                if dep not in for_this_package:
                    msg = 'Plugin {} depends on {}, but is not part of package {}'.format(plugin_name, dep, name)
                    util.warning(msg)

    # compile plugins
    compiled_count = 0
    for name in plugins_to_compile:
        plugin = plugins[name]
        if plugin.compile(compiler, plugin_build_dir):
            compiled_count += 1

    # build packages
    for name in packages_to_build:
        package = packages[name]
        print('Building package {}'.format(name))
        package.create(OUTPUT_DIR, filelist, packages, plugins)

    if len(plugins) == 0:
        util.warning('No plugins were found in {}.'.format(
            os.path.join(config_dir, CONFIG_NAME)))
    elif compiled_count == 0:
        print('All plugins up to date.')


def find_plugin_deps(package, packages_dict):
    plugins = set()
    for p in package.plugins:
        plugins.add(p)
    for p in package.extends_list:
        if p not in packages_dict:
            err_msg = 'Package {} extends non-existent package {}'
            util.error(err_msg.format(package.name, p))

        plugins.update(find_plugin_deps(packages_dict[p], packages_dict))
    return plugins
