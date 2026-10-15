"""Installer for the collective.contact.plonegroup package."""

from setuptools import find_packages
from setuptools import setup

long_description = (
    open("README.rst").read() + "\n" + "Contributors\n"
    "============\n"
    + "\n"
    + open("CONTRIBUTORS.rst").read()
    + "\n"
    + open("CHANGES.rst").read()
    + "\n"
)


setup(
    name="collective.contact.plonegroup",
    version="2.0.0.dev0",
    description="Organizations and functions combinations to create plone groups",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: 6.2",
        "Framework :: Plone :: Addon",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="plone contact management group suffix",
    author="Ecreall, Entrouvert, IMIO",
    author_email="s.geulette@imio.be",
    url="https://github.com/collective/collective.contact.plonegroup",
    download_url="https://pypi.org/project/collective.contact.plonegroup",
    license="GPL",
    packages=find_packages("src", exclude=["ez_setup"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "collective.contact.core",
        "collective.contact.widget",
        "collective.eeafaceted.z3ctable",
        "collective.elephantvocabulary",
        "collective.z3cform.datagridfield",
        "imio.actionspanel",
        "imio.helpers > 0.61",
        "imio.pyutils",
        "plone.api",
        "plone.app.linkintegrity",
        "plone.app.registry",
        "plone.autoform",
        "plone.base",
        "plone.behavior",
        "plone.dexterity",
        "plone.formwidget.masterselect",
        "plone.indexer",
        "plone.memoize",
        "plone.registry",
        "plone.supermodel",
        "plone.theme",
        "plone.uuid",
        "plone.z3cform",
        "Products.CMFCore",
        "Products.CMFPlone",
        "Products.DCWorkflow",
        "Products.GenericSetup",
        "Products.PluggableAuthService",
        "Products.statusmessages",
        "z3c.form",
        "z3c.table",
        "Zope",
    ],
    extras_require={
        "test": [
            "collective.eeafaceted.z3ctable[test]",
            "ecreall.helpers.testing",
            "imio.prettylink",
            "plone.app.robotframework",
            "plone.app.testing",
            "plone.browserlayer",
            "plone.testing",
            "robotsuite",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
