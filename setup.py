from setuptools import setup

setup(
    name = 'Eyecatching',
    version = '1.0-beta',
    py_modules=['run'],
    install_requires=[
        'Click',
        'pillow',
    ],
    entry_points='''
        [console_scripts]
        run=run:main
    ''',
)
