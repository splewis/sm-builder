import base
import builder
import parser
import structbuilder

import os
import unittest


def test_package():
    dirpath = os.path.dirname(os.path.realpath(__file__))
    target = os.path.join(dirpath, 'testpackages', 'test_package')
    return target


class BuilderTests(unittest.TestCase):
    def test_find_plugin_deps(self):
        def fake_package(name, plugins):
            # TODO: this is downright idiotic
            return base.PackageContainer(name, plugins, {}, [], [], [], [], [], [], '', [], {}, [])

        # TODO: this should really test package inheritance too
        p1 = fake_package('p1', ['plugin1', 'plugin2', 'plugin3'])
        p2 = fake_package('p2', ['plugin1', 'plugin4', 'plugin3'])
        packages = {
            'p1': p1,
            'p2': p2,
        }

        expected = set(['plugin1', 'plugin2', 'plugin3'])
        self.assertEqual(expected, base.find_plugin_deps(p1, packages))


class ParserTests(unittest.TestCase):
    def test_examples(self):
        target = test_package()
        parser.parse_configs(target)

        packages = sorted(['test_package'])
        plugins = sorted(['test_plugin', 'test_plugin2'])

        self.assertEqual(packages, sorted(parser.Packages.keys()))
        self.assertEqual(plugins, sorted(parser.Plugins.keys()))


class BaseTests(unittest.TestCase):
    def test_templatize(self):
        text = """
        sv_tags {{myarg}}
        sv_deadtalk {{deadtalk}}
        """
        args = {
            'myarg': 'myinput',
            'deadtalk': '1',
        }
        actual = base.templatize(text, args)
        expected = """
        sv_tags myinput
        sv_deadtalk 1
        """
        self.assertEqual(expected, actual)


class OverallTest(unittest.TestCase):
    def test_overall(self):
        target = test_package()
        builder.perform_builds(target, compiler='spcomp')


class StructTests(unittest.TestCase):
    def test_text(self):
        name='MyStruct'
        fields=[
            ('a', 'int'),
            ('b', 'float'),
            ('c', 'char'),
            ('d', 'int[4]'),
        ]

        expected_output = ("""
#define CreateMyStruct() MyStruct:MyStruct_New()
#define MyStructFromArray(%1,%2) (MyStruct:GetArrayCell(%1, %2))

stock Handle MyStruct_New() {
    Handle dataList = CreateArray();
    PushArrayCell(dataList, 0);
    PushArrayCell(dataList, 0.0);
    PushArrayCell(dataList, 0);
    for(int i = 0; i < 4; i++)
        PushArrayCell(dataList, 0);
    return dataList;
}

stock int MyStruct_GetA(Handle mystruct_) {
    return GetArrayCell(mystruct_, 0);
}

stock float MyStruct_GetB(Handle mystruct_) {
    return GetArrayCell(mystruct_, 1);
}

stock char MyStruct_GetC(Handle mystruct_) {
    return GetArrayCell(mystruct_, 2);
}

stock void MyStruct_GetD(Handle mystruct_, int buffer[4]) {
    for (int i = 0; i < 4; i++)
        buffer[i] = GetArrayCell(mystruct_, i + 3);
}

stock void MyStruct_GetDAt(Handle mystruct_, int index) {
    return GetArrayCell(mystruct_, index + 3);
}

stock void MyStruct_SetA(Handle mystruct_, int value) {
    SetArrayCell(mystruct_, 0, value);
}

stock void MyStruct_SetB(Handle mystruct_, float value) {
    SetArrayCell(mystruct_, 1, value);
}

stock void MyStruct_SetC(Handle mystruct_, char value) {
    SetArrayCell(mystruct_, 2, value);
}

stock void MyStruct_SetD(Handle mystruct_, const int value[4]) {
    for (int i = 0; i < 4; i++)
        SetArrayCell(mystruct_, i + 3, value[i]);
}

stock void MyStruct_SetDAt(Handle mystruct_, int value, int index) {
    SetArrayCell(mystruct_, index + 3, value);
}

methodmap MyStruct < Handle {
    public int GetA() {
        return MyStruct_GetA(this);
    }

    public void SetA(int x_) {
        MyStruct_SetA(this, x_);
    }

    property int a {
        public set() = MyStruct_SetA;
        public get() = MyStruct_GetA;
    }

    public float GetB() {
        return MyStruct_GetB(this);
    }

    public void SetB(float x_) {
        MyStruct_SetB(this, x_);
    }

    property float b {
        public set() = MyStruct_SetB;
        public get() = MyStruct_GetB;
    }

    public char GetC() {
        return MyStruct_GetC(this);
    }

    public void SetC(char x_) {
        MyStruct_SetC(this, x_);
    }

    property char c {
        public set() = MyStruct_SetC;
        public get() = MyStruct_GetC;
    }

    public void GetD(int buffer[4]) {
        MyStruct_GetD(this, buffer);
    }

    public int GetDAt(int index) {
        return MyStruct_GetDAt(this, index);
    }

    public void SetD(const int value[4]) {
        MyStruct_SetD(this, value);
    }

    public void SetDAt(int value, int index) {
        MyStruct_SetDAt(this, value, index);
    }

}""")

        def clean_code(code):
            tmp = code.strip()
            tmp.replace('\t', '    ')
            return tmp

        actual_output = structbuilder.get_struct_code(name, fields)

        actual_list = actual_output.strip().split('\n')
        expected_list = expected_output.strip().split('\n')
        print actual_output

        self.assertEqual(len(actual_list), len(expected_list))

        for i in range(0, len(actual_list)):
            actual = clean_code(actual_list[i])
            expected = clean_code(expected_list[i])
            self.assertEqual(actual, expected)

        self.assertEqual(clean_code(actual_output), clean_code(expected_output))


if __name__ == "__main__":
    unittest.main()
