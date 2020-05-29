# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


import os
import re
import shutil

from pkg_resources import parse_version
import pip


if parse_version(pip.__version__) < parse_version('19.3.0'):
    raise ValueError('Pip should be version 19.3.0 or higher')

from pip._internal import main as pip_main  # pip >= 10

from setuptools import setup, find_packages, Command


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_usd', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


STAGING_PATH = os.path.join(
    BUILD_PATH, 'ftrack-templated-structure-{0}'.format(VERSION)
)


class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        import setuptools_scm
        release = setuptools_scm.get_version()
        VERSION = '.'.join(release.split('.')[:3])
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        pip_main.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies')
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-templated-structure-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2017-2020 ftrack

__version__ = {version!r}
'''

# Call main setup.
setup(
    name='ftrack-usd',
    version=VERSION,
    description='ftrack usd  example.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, integration, connect',
    url='https://bitbucket.org/l_angeli/ftrack-usd-action',
    author='ftrack',
    author_email='lorenzo.angeli@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_required = [
        'setuptools>=30.3.0',
        'setuptools_scm',
    ],
    install_requires=[
        'ftrack-action-handler',
    ],
    tests_require=[
    ],
    zip_safe=False,
    use_scm_version={
        'write_to': 'source/ftrack_usd/_version.py',
        'write_to_template': version_template,
    },
    cmdclass={
        'build_plugin': BuildPlugin,
    },
    python_requires='>= 2.7.9, < 3.0'
)