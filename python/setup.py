import setuptools

with open('../README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='distant_vfx',
    version='0.2.3',
    author='Mark Livolsi',
    author_email='mark.c.livolsi@gmail.com',
    description='A toolkit for the Distant VFX team.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/marklivolsi/distant-vfx',
    packages=setuptools.find_packages(),
    classifiers=(
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ),
    python_requires='>=3.6'
)