import os
import re
import sys

from setuptools import setup

with open('lilvlib/__init__.py', 'r') as fh:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fh.read(), re.MULTILINE).group(1)

buildid = os.environ.get('SETUP_BUILD_ID', None)
version = '{0}.dev{1}'.format(version, buildid) if buildid else version


def main():
    setup(
        name='mod-lilvlib',
        version=version,
        description='A set of helper methods to extract plugin and pedalboard data from TTLs using lilv',
        author='Falktx',
        author_email='falktx@gmail.com',
        license='MIT',
        packages=['lilvlib'],
        install_requires=[],  # lilv must be installed locally but cannot be resolved by PIP
        entry_points={'console_scripts': ['lilvlib = lilvlib.lilvlib:main']},
        classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
        ],
        url='https://github.com/moddevices/lilvlib',
    )


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'package_version':
        print(version)
        exit(0)
    main()
