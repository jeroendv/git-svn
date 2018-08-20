"""
pip-svn has some convenience functions to initialize a git-svn bridge inside a svn working copy
"""
import sys
from setuptools import setup

if sys.version_info < (3,5):
    sys.exit('Sorry, Python < 2.7 is not supported')

setup(
    name='git-svn',
    version='1.0',
    url='http://...',
    license=None,
    author='jeroen_devlieger',
    author_email='jeroen.devlieger@nikon.com',
    description="__doc__.strip('\n')",
    packages=[
        'git_svn'
    ],
    entry_points={
        'console_scripts': [
            'git-svn-init = git_svn.init:main',
            "git-svn-checkoutHistoricSvnExternals = git_svn.checkoutHistoricSvnExternals:main",
            'git-svn-migrateSvnIgnore = git_svn.migrateSvnIgnore:main',
            'git-svn-syncSvnWithGit = git_svn.syncSvnWithGit:main',
            'git-svn-checkoutHistoricRev = git_svn.checkoutHistoricRev:main',
            'git-svn-checkoutSvnExternals = git_svn.checkoutSvnExternals:main',
            'git-svn-info = git_svn.info:main',
            'git-svn-svnSparseCheckout = git_svn.SvnSparseCheckout:main'
        ],
    },
    #include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'packaging',
        'pip',
        'six',
        'pyyaml'
    ],
    setup_requires=[
        "pytest-runner"
    ],
    tests_require=[
        "pytest"
    ],
    python_requires='>= 3.5',
    classifiers=[
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 1 - Planning',
        #'Development Status :: 2 - Pre-Alpha',
        #'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Programming Language :: Python',
        #'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.3',
        #'Programming Language :: Python :: 2.4',
        #'Programming Language :: Python :: 2.5',
        #'Programming Language :: Python :: 2.6',
        #'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.0',
        #'Programming Language :: Python :: 3.1',
        #'Programming Language :: Python :: 3.2',
        #'Programming Language :: Python :: 3.3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        #'Intended Audience :: System Administrators',
        #'License :: OSI Approved :: BSD License',
        #'Operating System :: OS Independent',
        #'Topic :: System :: Systems Administration',
    ]
)
