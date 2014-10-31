from distutils.core import setup

setup(
    name='smbuilder',
    version='0.0.1',
    description='',
    author='Sean Lewis',
    author_email='splewis@utexas.edu',
    url='https://github.com/splewis/sm-builder',
    scripts=['scripts/smbuilder', 'scripts/smuploader', 'scripts/smdownload'],
    packages=['smbuilder'],
    package_dir={'smbuilder': 'src/smbuilder'},
    package_data={'smbuilder': ['plugins/*.sp', 'plugins/smbuild']},
    requirements=['jinja2', 'appdirs'],
)
