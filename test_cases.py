import unittest
import smbuilder


class SMBuilderTests(unittest.TestCase):
    def test_overall(self):
        smbuilder.perform_builds('test', 'spcomp')


if __name__ == "__main__":
    unittest.main()
