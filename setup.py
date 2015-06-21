#
#   Copyright 2015 by Douglas Fraser <dfraser@douglas-fraser.com>
#

from setuptools import setup, find_packages

setup(
    name="mezzanine-twitterplus",
    version="0.5.0",
    description="Mixins for Mezzanine admin for Twitter support such as tweeting images",
    author="Douglas Fraser",
    author_email="dfraser@douglas-fraser.com",
    url="http://github.com/drfraser/mezzanine-twitterplus",
    license=open('LICENSE', 'r').read(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=['mezzanine>=3.1.9'],
    keywords='twitter api mezzanine',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
