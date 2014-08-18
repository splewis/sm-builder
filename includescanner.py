import util

import os


# TODO: guard against infinite loops (detect cycles early)
def find_last_time_modified(filename):
    "Finds the latest time this source file was modified, including all includes."
    try:
        latest_time = os.path.getmtime(filename)
        with open(filename) as f:
            to_read = []
            lines = f.read().split('\n')
            for line in lines:
                if '#include' in line:
                    arg = line.split(' ')[1].strip()
                    if arg.startswith('<'):
                        # TODO: also read system includes
                        pass
                    elif arg.startswith('\"'):
                        include_file = arg.replace('\"', '')
                        include_file = os.path.join(os.path.dirname(filename), include_file)
                        to_read.append(include_file)

            for file in to_read:
                if not os.path.exists(file):
                    util.error('Missing file: {}\n\tincluded from {}'.format(file, filename))

                latest_time = max(latest_time, find_last_time_modified(file))

        return latest_time

    except OSError as e:
        print e
        util.error('Missing file: {}'.format(filename))

