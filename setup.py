from setuptools import setup

setup(
    name='mod-lilvlib',
    version='0.0.4',
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
    url='https://github.com/portalmod/lilvlib',
)
