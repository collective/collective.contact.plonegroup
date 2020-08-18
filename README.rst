.. image:: https://secure.travis-ci.org/collective/collective.contact.plonegroup.png
    :target: http://travis-ci.org/collective/collective.contact.plonegroup

.. image:: https://coveralls.io/repos/github/collective/collective.contact.plonegroup/badge.svg?branch=master
    :target: https://coveralls.io/github/collective/collective.contact.plonegroup?branch=master

=============================
collective.contact.plonegroup
=============================

Introduction
============

A Plone add-on that manage organizations and functions, leading to corresponding plone groups creation.
This product makes the link between:

* `collective.contact.core`_ : organization definition containing your organization services (multiple levels)
* `dexterity.localrolesfield`_ : field presenting a list of services for which a local role can be given

How-to
======

First, create a directory in your site (object from collective.contact.core). This directory will contain all the informations related to your contacts.

You can then add your organization in it (with a specific id equal to 'plonegroup-organization').
An organization can contain organizations (such as services, divisions or department).

In the collective.contact.plonegroup configuration panel, you have to :

* select some services of your organization to be used in localroles field
* define some function labels that will be used in each selected organization

When submitting, for each organization - function combination, a plone group is created with the id "organization-uid"_"function-id" and name "organizations-name" ("function-name").

The generated plone groups will be used in localroles field, where some local roles can be given to some function for each selected service.

Installation
============

* Add collective.contact.plonegroup to your eggs.
* Re-run buildout.
* Install the product in your plone site.

Credits
=======

Have an idea? Found a bug? Let us know by `opening a ticket`_.

.. _`opening a ticket`: https://github.com/collective/collective.contact.plonegroup/issues
.. _`collective.contact.core`: https://github.com/collective/collective.contact.core
.. _`dexterity.localrolesfield`: https://github.com/collective/dexterity.localrolesfield
