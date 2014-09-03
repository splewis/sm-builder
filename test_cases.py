import base
import builder
import parser
import smbuilder

import os
import unittest


def check_file_contents(testclass, filename, expected):
    testclass.assertTrue(os.path.exists(filename))
    with open(filename) as f:
        fileinput = map(lambda line: line.strip(), f.readlines())
        testclass.assertEqual(expected, fileinput)



class BuilderTests(unittest.TestCase):
    def test_find_plugin_deps(self):
        def fake_package(name, plugins):
            # TODO: this is downright idiotic
            return base.PackageContainer(name, plugins, {}, [], [], [], [], [], [], '', [], {})

        # TODO: this should really test package inheritance too
        p1 = fake_package('p1', ['plugin1', 'plugin2', 'plugin3'])
        p2 = fake_package('p2', ['plugin1', 'plugin4', 'plugin3'])
        packages = {
            'p1': p1,
            'p2': p2,
        }

        expected = set(['plugin1', 'plugin2', 'plugin3'])
        self.assertEqual(expected, builder.find_plugin_deps(p1, packages))


class ParserTests(unittest.TestCase):
    pass


class BaseTests(unittest.TestCase):
    pass


class OverallTests(unittest.TestCase):
    def test_overall(self):
        smbuilder.perform_builds('test', 'spcomp')

        package_dir = os.path.join('builds', 'test_package')

        # check server.cfg
        expected = ['hostname myserver', 'sv_alltalk 1', 'sv_deadtalk 0']
        check_file_contents(self, os.path.join(package_dir, 'cfg', 'server.cfg'), expected)


if __name__ == "__main__":
    unittest.main()
