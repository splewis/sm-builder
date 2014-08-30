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


# Taken from http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
def copytree(src, dst, symlinks=False, ignore=None):
    """Copies a tree of files to a destination."""
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
                shutil.copy2(s, d)


def copy_package_files(list, dir):
    for f in list:
        if os.path.isdir(f):
            copytree(f, dir)
        else:
            shutil.copy2(f, dir)


def file_to_plugin_name(filename):
    plugin_name = os.path.basename(filename)
    return os.path.splitext(plugin_name)[0]


# Taken from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
