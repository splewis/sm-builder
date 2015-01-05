import util

import os


# TODO: guard against infinite loops (detect cycles early)
def find_last_time_modified(filename):
    """
    Finds the latest time this source file was modified,
    including all includes.
    """
    visited = set([filename])
    time = _find_last_time_modified(filename, visited)
    base = os.path.dirname(filename)
    visited = map(lambda f: os.path.relpath(f, base), visited)
    return time, visited


def _find_last_time_modified(filename, visited):
    try:
        latest_time = os.path.getmtime(filename)
        with open(filename) as f:
            to_read = []
            lines = f.read().split('\n')
            for line in lines:
                optional = '#tryinclude' in line
                if '#include' in line or optional:
                    arg = line.split(' ')[1].strip()
                    if arg.startswith('<'):
                        # TODO: also read system includes
                        pass
                    elif arg.startswith('\"'):
                        include_file = arg.replace('\"', '')
                        include_file = os.path.join(os.path.dirname(filename), include_file)

                        # dirty hack to allow include of things without filenames
                        name, extension = os.path.splitext(include_file)
                        if not extension:
                            include_file += '.inc'

                        to_read.append((include_file, optional))
                        if os.path.exists(include_file):
                            visited.add(include_file)

            for file, optional in to_read:
                if not os.path.exists(file) and not optional:
                    util.error('Missing file: {}\n\tincluded from {}'.format(file, filename))

                if os.path.exists(file):
                    latest_time = max(latest_time, _find_last_time_modified(file, visited))

        return latest_time

    except OSError as e:
        print(e)
        util.error('Missing file: {}'.format(filename))
