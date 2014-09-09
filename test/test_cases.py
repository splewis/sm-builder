# import smbuilder
import smbuilder.base
import smbuilder.builder
import smbuilder.parser

import os
import unittest


class BuilderTests(unittest.TestCase):
    def test_find_plugin_deps(self):
        def fake_package(name, plugins):
            # TODO: this is downright idiotic
            return smbuilder.base.PackageContainer(name, plugins, {}, [], [], [], [], [], [], '', [], {}, True)

        # TODO: this should really test package inheritance too
        p1 = fake_package('p1', ['plugin1', 'plugin2', 'plugin3'])
        p2 = fake_package('p2', ['plugin1', 'plugin4', 'plugin3'])
        packages = {
            'p1': p1,
            'p2': p2,
        }

        expected = set(['plugin1', 'plugin2', 'plugin3'])
        self.assertEqual(expected, smbuilder.builder.find_plugin_deps(p1, packages))


class ParserTests(unittest.TestCase):
    pass


class BaseTests(unittest.TestCase):
    def test_templatize(self):
        text = """
        sv_tags %myarg%
        hostname %myarg%
        $sv_deadtalk$
        $sv_alltalk$
        """
        args = {
            'myarg': 'myinput',
            'sv_deadtalk': '1',
            'sv_alltalk': '1',
        }
        actual = smbuilder.base.templatize(text, args)
        expected = """
        sv_tags myinput
        hostname myinput
        sv_deadtalk 1
        sv_alltalk 1
        """

if __name__ == "__main__":
    unittest.main()
