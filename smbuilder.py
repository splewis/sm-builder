#!/usr/bin/env python

import builder
import parser

import argparse
import os
import shutil


def perform_builds(target, compiler):
    plugins, packages = parser.parse_configs(target)
    smbuildfile = os.path.join(target, parser.CONFIG_NAME)
    builder.build(smbuildfile, compiler, plugins, packages)


def clean():
    if os.path.exists(builder.OUTPUT_DIR):
        shutil.rmtree(builder.OUTPUT_DIR)


def main():
    parser = argparse.ArgumentParser(
        description='A sourcemod build and packaging tool.')
    parser.add_argument('target', nargs='?')
    parser.add_argument('-c', '--compiler', default='spcomp',
                        help='Sourcepawn compiler to use.')
    args = parser.parse_args()

    if not args.target:
        args.target ='.'

    if args.target == 'clean':
        clean()
    else:
        perform_builds(args.target, args.compiler)


if __name__ == '__main__':
    main()
