[![Build Status](https://travis-ci.org/splewis/sm-builder.svg?branch=master)](https://travis-ci.org/splewis/sm-builder)

This is a simple build/package tool for managing SourceMod plugins and servers. **It is still very much a work in progress. Don't try to use it unless you want to contribute to its development.**

It uses a simple python-based syntax inspired by Google's [Blaze](http://google-engtools.blogspot.fr/2011/08/build-in-cloud-how-build-system-works.html) tool.

General philosophy:
- Convention over configuration
- Allows custom rules
- Simple configuration syntax
- User friendly (especially when presenting errors - no python stack traces!)
- Useful to both public-plugin developers and server administrators


### A brief example

Consider a plugin (for example: my PugSetup plugin for CS:GO) that lives in the ``scripting`` directory.

You also might have some files under ``cfg``, like ``server.cfg``.


**server.cfg**:
```
$hostname$
sv_alltalk 1
mp_autokick 0
```

**smbuild:**
```
Plugin(name='pugsetup', source='scripting/pugsetup.sp')

Package(name='pugsetup-server',
        plugins=['pugsetup'],
        cfg='pugsetup_cfgs',
        args={
        	'hostname': '10 man server',
        },
)
```

From the directory this all lives in, invoking ``smbuilder`` will
- compile (if needed) ``scripting/pugsetup.sp``
- copy the files from ``pugsetup_cfgs`` to the output ``cfg`` directory
- replace (in ``server.cfg``), ``hostname`` with ``hostname 10 man server``

This will produce the output package, which will live in ``builds/pugsetup-server``, which will have both an ``addons`` directory and a ``cfg`` directory under it, matching the server file layout.


### Installation
For a unix-style system, you should run:
- ``git clone https://github.com/splewis/sm-builder``
- ``cd sm-builder``
- ``python setup.py install``
- You're done! You can now invoke ``smbuilder`` on the command line.

Windows support **may** come later. It shouldn't take much to get it to work, but there may be small issues to work out before I can claim it works on windows.


### Command line usage

- ``smbuilder`` will run the smbuild file in the current directory.
- ``smbuilder <target>`` will run the smbuild file in the given target directory

#### Flags:
- ``--compiler (-c)`` specifies a sourcepawn compiler to use (default: spcomp)


### Examples
Some examples are my sourcemod plugin projects:
- https://github.com/splewis/csgo-multi-1v1/blob/master/smbuild
- https://github.com/splewis/csgo-pug-setup/blob/master/smbuild
- https://github.com/splewis/smart-player-reports/blob/master/smbuild


### Usage
You may define a ``Plugin`` or ``Package``.

Registering a ``Plugin`` have the following named arguments:
- ``source``: **required**, source code file for the plugin
- ``name``: unique name that identifies the plugin, if not defined, the filename (minus extension) is used as the name
- ``compiler``: compiler that the plugin should use (if none defined, the command-line provided compiler is used)
- ``deps``: names of other plugins that this plugin relies on (i.e. runtime dependencies)


Registering a ``Package`` has the following named arguments:
- ``name``: **required**, unique name that identifies the package
- ``plugins``: list of plugin names the package contains
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


### How to use template arguments
In your template file, you may name a variable by surrounding it with ``%`` character or ``$`` characters. A ``%`` will purely replace, while a ``$`` will simply remove the ``$`` and add a space, then the value.

By example, the following input:
```
Package(
    name='mypackage',
    args={
        'hostname': 'myserver',
        'sv_deadtalk': '0',
    },
)
```

```
hostname %hostname%
$sv_deadtalk$
```

will produce an output file of:
```
hostname myserver
sv_deadtalk 0
```
