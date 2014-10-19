import os
import shutil


def warning(text):
    """Prints a warning message to the console."""
    print(bcolors.WARNING + 'WARNING: ' + bcolors.ENDC + text)


def error(text, die=True):
    """Prints an error message to the console and kills the process if wanted."""
    print(bcolors.FAIL + 'ERROR: ' + bcolors.ENDC + text)
    if die:
        exit(1)


def mkdir(*args):
    """Creates a directory path if it doesn't exist."""
    path = ''.join(os.path.join(args))
    if not os.path.exists(path):
        os.makedirs(path)


def copytree(src, dst):
    """Copies a tree of files to a destination."""
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copy2(s, d)


def safe_copytree(src, dst):
    """Copies a tree of files to a destination, ignoring any non existing paths."""
    if not src or not dst or not os.path.exists(src):
        return
    else:
        copytree(src, dst)


def copy_package_files(list, dir):
    for f in list:
        if os.path.isdir(f):
            copytree(f, dir)
        else:
            shutil.copy2(f, dir)


def list_files_recursively(path):
    results = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            results.append(os.path.relpath(os.path.join(dirname, filename), path))
    return results


def file_to_plugin_name(filename):
    plugin_name = os.path.basename(filename)
    return os.path.splitext(plugin_name)[0]


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
