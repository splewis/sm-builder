[![Build Status](https://travis-ci.org/splewis/sm-builder.svg?branch=master)](https://travis-ci.org/splewis/sm-builder)

**This is still very much a work in progress. Don't try to use it unless you want to contribute to its development. Currently, this only targets python2 and unix-like systems**

**smbuilder** is a build/package tool for managing SourceMod plugins and servers. It works as a command-line tool that:
- reads a configuration file
- compiles any changed plugins
- creates packages, which are just sets of files ready to be uploaded to a server

#### Why is it helpful?
- Helps you have 1 file that defines what goes on a server, by creating a package for it
- Convenient way to manage configuration files
- Intelligent templating of config files (using [Jinja2](http://jinja.pocoo.org/)), which makes it easy to reuse files with slight changes for different servers

#### What doesn't it do?
- Doesn't upload files to a server (a script to do this may come in the future though)
- Doesn't deal with old files on a server - they won't get removed easily (maybe in the future I'll have a way to handle that)
- Doesn't manage your install of the sourcemod compiler or 3rd party include files
- Doesn't do anything with extensions

The config files are just python files, so you can use any python syntax you want in them.

#### General philosophy:
- Convention over configuration
- Simple configuration syntax
- User friendly (especially when presenting errors - avoid python stack traces!)
- Useful to both plugin developers and server administrators


## A brief example

Consider a plugin (for example: my [PugSetup](https://github.com/splewis/csgo-pug-setup) plugin for CS:GO) that lives in the ``scripting`` directory.

You also might have some files under ``cfg``, like ``server.cfg``.


**server.cfg**:
```
hostname {{name}}
sv_alltalk 1
mp_autokick 0
```

**smbuild:**
```
Plugin(name='pugsetup', source='scripting/pugsetup.sp')

Package(name='pugsetup-server',
        plugins=['pugsetup'],
        args={
        	'name': '10 man server',
        },
)
```

From the directory this all lives in, invoking ``smbuilder`` will
- compile (if needed) ``scripting/pugsetup.sp``
- copy the files from ``pugsetup_cfgs`` to the output ``cfg`` directory
- replace (in ``server.cfg``), ``hostname`` with ``hostname 10 man server``

This will produce the output package, which will live in ``builds/pugsetup-server``, which will have both an ``addons`` directory and a ``cfg`` directory under it, matching the server file layout.


## Installing a development version
For a unix-style system, you should run:

1. Clone the repository: ``git clone https://github.com/splewis/sm-builder``
1. Move into the repo: ``cd sm-builder``
1. Install [pip](http://pip.readthedocs.org/en/latest/installing.html) for managing the python dependencies: ``sudo apt-get install python-pip`` for debian and ubuntu
1. Install python dependencies if needed: ``sudo pip install -r requirements.txt``
1. Install smbuiler: ``sudo python setup.py install``
1. You're done! You can now invoke ``smbuilder`` on the command line.

You may still need to configure a SourcePawn compiler, so read on below for how to do that.

Windows support **may** come later. It shouldn't take much to get it to work, but there may be small issues to work out before I can claim it works on windows.


## Command line usage

- ``smbuilder`` will run the smbuild file in the current directory.
- ``smbuilder <target>`` will run the smbuild file in the given target directory

Note that the output is always in the ``builds`` directory.

#### Flags and settings:

The first time the program is run, it will produce a file in a user-config directory. For linux, this will generally be ``~/.config/smbuilder.ini``.

Example first run:
```
splewis-laptop csgo-retakes $ smbuilder
Settings written to /home/splewis/.config/smbuilder.ini
```

You can also set things from command line flags (these overrule the config file settings):
- ``--compiler (-c)`` specifies a sourcepawn compiler to use (default: ``spcomp``)

You may want to add the path of of your sourcemod compiler to the system path, something like:
``PATH+=":/home/splewis/sm/addons/sourcemod/scripting"``


## Examples
Examples from smbuilder's testing:
- [test_package](src/smbuilder/testpackages/test_package/smbuild)
- [test_package2](src/smbuilder/testpackages/test_package2/smbuild)

Some examples are my sourcemod plugin projects:
- https://github.com/splewis/csgo-multi-1v1/blob/master/smbuild
- https://github.com/splewis/csgo-pug-setup/blob/master/smbuild
- https://github.com/splewis/smart-player-reports/blob/master/smbuild


## Usage
You may define a ``Plugin`` or ``Package``.

Registering a ``Plugin`` have the following named arguments:
- ``source``: source code file for the plugin (cannot be used if ``binary`` is used)
- ``binary``: binary file for the plugin (cannot be used if ``source`` is used)
- ``name``: unique name that identifies the plugin, if not defined, the filename (minus extension) is used as the name
- ``deps``: names of other plugins that this plugin relies on (i.e. runtime dependencies)


Registering a ``Package`` has the following named arguments:
- ``name``: **required**, unique name that identifies the package
- ``plugins``: list of plugin names the package contains
- ``disabled_plugins``: list of plugin names that should be disabled (not inherited)
- ``extends``: inherited base packages
- ``cfg``: directory name to bring files into the package ``cfg`` directory
- ``configs``: directory name to bring files from ``addons/sourcemod/configs`` from
- ``data``: directory name to bring files from ``addons/sourcemod/data`` from
- ``gamedata``: directory name to bring files from ``addons/sourcemod/gamedata`` from
- ``translations``: directory name to bring files from ``addons/sourcemod/translations`` from
- ``sources``: list of source code files to also compile into the package (this is a shortcut for creating a ``Plugin`` for each one)
- ``args``: dictionary of arguments to replace in non-binary files
- ``filegroups``: dictionary of output directory name -> list of input files to package into the build


You may also include plugins/packages from another directory using ``Include``.


## How to use templates

[Jinja2](http://jinja.pocoo.org/) is used for templating config files. Here is an brief example:

```
Package(
    name='mypackage',
    args={
        'name': 'myserver',
        'competitive': True,
    },
)
```

some file in the `cfg` directory:
```
hostname {{name}}

{% if competitive %}
sv_alltalk 0
sv_deadtalk 1
{% else %}
sv_alltalk 1
sv_deadtalk 0
{% endif %}
```

will produce a corresponding output file of:
```
hostname myserver
sv_alltalk 0
sv_deadtalk 1
```

With this strategy you can reuse different configuration values and files in different packages, without making dozens of files.

There is a special arguments you can use in config files: ``plugin_binaries``, which is set to the list of plugin binary filenames in the package.
