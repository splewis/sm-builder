[![Build Status](https://travis-ci.org/splewis/sm-builder.svg?branch=master)](https://travis-ci.org/splewis/sm-builder)

This is a simple build/package tool for managing SourceMod plugins and servers. It is still very much a work in progress. Don't try to use it unless you want to contribute to its development.

It uses a simple python-based syntax inspired by Google's internal [Blaze](http://google-engtools.blogspot.fr/2011/08/build-in-cloud-how-build-system-works.html) tool.

General philosophy:
- Convention over configuration
- Allows custom rules
- Simple configuration syntax
- User friendly (especially when presenting errors - no python stack traces!)
- Useful to both public-plugin developers and server administrators



### Installation
For a unix-style system, you should run:
- ``git clone https://github.com/splewis/sm-builder``
- ``cd sm-builder``
- ``python setup.py install``

- You're done! You can now invoke ``smbuilder`` on the command line.

Windows support **may** come later. It shouldn't take much to get it to work, but there may be small issues to work out before I can claim it works on windows.


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
- ``template_args``: dictionary of template arguments to replace in files that match one of the ``template_files``
- ``filegroups``: dictionary of output directory name -> list of input files to package into the build


You may also include plugins/packages from another directory using ``Include``.


### How to use template arguments
In your template file, you may name a variable by surrounding it with ``%`` character or ``$`` characters. A ``%`` will purely replace, while a ``$`` will simply remove the ``$`` and add a space, then the value.

By example, the following input:
```
Package(
    name='mypackage',
    template_args={
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
