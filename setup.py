from setuptools import setup

#entry config: cmd = file:method
setup(
    name = 'Eyecatching',
    version = '1.0',
    py_modules=['eyecatching'],
    install_requires=[
        'Click',
        'Pillow',
        'Numpy',
        'Scipy',
        'opencv-python',
        'pandas'
    ],
    entry_points='''
        [console_scripts]
        eyecatching=eyecatching:cli 
    ''',
)
