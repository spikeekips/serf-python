from setuptools import setup


setup(
    name='serf',
    version='0.1',
    description='serf client for python',
    long_description=file('README.md', ).read(),
    author='Spike^ekipS',
    author_email='spikeekips@gmail.com',
    url='https://github.com/spikeekips',
    license='License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
    install_requires=(
            'msgpack-python',
        ),
    packages=('serf', ),
    package_dir={'': 'src', },
)


