from setuptools import setup

#entry config: cmd = file:method
setup(
    name = 'Eyecatching',
    version = '1.0-beta',
    py_modules=['eyecatching'],
    install_requires=[
        'Click',
        'Pillow',
        'Numpy',
        'Scipy',
    ],
    entry_points='''
        [console_scripts]
        eyecatching=eyecatching:cli 
    ''',
)
