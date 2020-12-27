import setuptools

setuptools.setup(
    name='distant_vfx',
    version='0.2.9',
    author='Mark Livolsi',
    author_email='mark.c.livolsi@gmail.com',
    description='A toolkit for the Distant VFX team.',
    long_description='A toolkit for the Distant VFX production team.',
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
