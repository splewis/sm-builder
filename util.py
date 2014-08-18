import os


def warning(text):
    print bcolors.WARNING + 'WARNING: ' + bcolors.ENDC + text


def error(text):
    print bcolors.FAIL + 'ERROR: ' + bcolors.ENDC + text
    exit(1)


def mkdir(*args):
    path = ''.join(os.path.join(args))
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# Taken from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
