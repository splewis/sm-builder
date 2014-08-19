[![Build Status](https://travis-ci.org/splewis/sm-builder.svg?branch=master)](https://travis-ci.org/splewis/sm-builder)

This is a simple build/package tool for managing SourceMod plugins and servers.

It uses a simple python-based syntax inspired by Google's [Blaze](http://google-engtools.blogspot.fr/2011/08/build-in-cloud-how-build-system-works.html) tool.

This is a work in progress. Unless you want to contribute, don't try to use it just yet.

General philosophy:
- Convention over configuration
- Allows custom rules
- Simple configuration syntax
- User friendly (especially when presenting errors - no python stack traces!)


### Installation
For a unix-style system, you should:
- Clone the repository: e.g. ``https://github.com/splewis/sm-builder``
- Add the new sm-builder directory that was just created to your system $PATH variable

  (for example, I have this line in my .bashrc file: ``
PATH+=":/home/splewis/git/sm-builder"``)

- You're done! You can now invoke ``smbuilder`` on the command line. Note that smbuilder is just a symlink to smbuilder.py.


### Examples
Some examples are my sourcemod plugin projects:
- https://github.com/splewis/csgo-pug-setup/blob/master/smbuild
- https://github.com/splewis/smart-player-reports/blob/master/smbuild



