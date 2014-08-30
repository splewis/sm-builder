import base
import builder
import parser
import smbuilder

import unittest


class BuilderTests(unittest.TestCase):
    pass


class ParserTests(unittest.TestCase):
    pass


class OverallTests(unittest.TestCase):
    def test_overall(self):
        smbuilder.perform_builds('test', 'spcomp')


if __name__ == "__main__":
    unittest.main()
