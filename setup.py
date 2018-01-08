import sys
from setuptools import setup

_requires = [
        'msgpack',
    ]

if sys.version_info < (2, 7, 0, ) :
    _requires.append('ordereddict', )


setup(
    name='serf-python',
    version='0.2.2',
    description='serf client for python',
    long_description="""
For more details, please see https://github.com/spikeekips/serf-python .
    """,
    author='Spike^ekipS',
    author_email='spikeekips@gmail.com',
    url='https://github.com/spikeekips/serf-python',
    license='License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
    install_requires=tuple(_requires, ),
    packages=('serf', ),
    package_dir={'': 'src', },
)


