from setuptools import setup

setup(
    name = 'Eyecatching',
    version = '1.0-beta',
    py_modules=['eyecatching'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        eyecatching=eyecatching:main
    ''',
)
