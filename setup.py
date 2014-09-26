from distutils.core import setup

setup(
    name='smbuilder',
    version='0.0.1',
    description='',
    author='Sean Lewis',
    author_email='splewis@utexas.edu',
    url='https://github.com/splewis/sm-builder',
    scripts=['scripts/smbuilder'],
    packages=['smbuilder'],
    package_dir={'smbuilder': 'src/smbuilder'},
    requirements=['jinja2'],
)
