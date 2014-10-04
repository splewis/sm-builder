import base
import parser
import util

import os


OUTPUT_DIR = 'builds'


def perform_builds(target='.', compiler='spcomp', filelist=False):
    """Main library entrance to build packages."""
    plugins, packages = parser.parse_configs(target)
    smbuildfile = os.path.join(target, parser.CONFIG_NAME)
    build(smbuildfile, compiler, filelist, plugins, packages)


def build(smbuildfile, compiler, filelist, plugins, packages):
    """Performs the entire build process."""
    # setup directory structure, execute user-configurationsz
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
        for_this_package = base.find_plugin_deps(packages[name], packages)
        for plugin_name in for_this_package:
            plugins_to_compile.add(plugin_name)

            if plugin_name not in plugins:
                err = 'Package {} uses plugin {}, but it does not exist'.format(name, plugin_name)
                util.error(err)

            # also make sure plugin dependencies are met by the package
            for dep in plugins[plugin_name].deps:
                if dep not in for_this_package:
                    msg = 'Plugin {} depends on {}, but is not part of package {}'.format(plugin_name, dep, name)
                    util.warning(msg)

    # also compile any plugins from this smbuildfile
    for plugin_name in plugins:
        if plugins[plugin_name].smbuildfile == smbuildfile:
            plugins_to_compile.add(plugin_name)

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

