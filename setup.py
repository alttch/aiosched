__version__ = '0.0.25'

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(name='aiosched',
                 version=__version__,
                 author='Altertech',
                 author_email='div@altertech.com',
                 description='asyncio job scheduler',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://github.com/alttch/aiosched',
                 packages=setuptools.find_packages(),
                 license='MIT',
                 install_requires=[],
                 classifiers=('Programming Language :: Python :: 3',
                              'License :: OSI Approved :: MIT License',
                              'Topic :: Software Development :: Libraries'))
