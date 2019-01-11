Changelog
=========


1.13 (2019-01-11)
-----------------

- Use unrestrictedSearchResults to check link integrity.
  [sgeulette]
- Added helpers config.get_registry_organizations,
  config.get_registry_functions, config.set_registry_organizations and
  config.set_registry_functions to easily get and set organizations/functions
  registry records.
  [gbastien]

1.12 (2018-12-11)
-----------------

- Added parameter `kept_org_uids` to `utils.get_organizations` to only keep
  organizations having defined UID.
  [gbastien]
- Sort `collective.contact.plonegroup.selected_organization_services`
  vocabulary by value title.
  [gbastien]
- Display the organization UID next to title in the `suborganizations` view.
  [gbastien]

1.11 (2018-11-20)
-----------------

- In utils.get_organizations, call uuidsToObjects with ordered=True to get
  organizations in correct order because the catalog query is not sorted.
  [gbastien]
- Fixed migration that adds 'fct_orgs' to functions.
  [gbastien]

1.10 (2018-10-12)
-----------------

- Removed grok for OwnOrganizationServicesVocabulary.
  [gbastien]
- Added utils.get_organization to get an organization corresponding
  to a given plone_group_id.
  [gbastien]
- Added utils.get_organizations to get every plonegroup organizations.  It is
  possible to get every selectable or selected organizations, as objects or not
  and for which a particular linked Plone group (suffix) is not empty.
  [gbastien]
- Added utils.get_all_suffixes that returns every defined functions ids.
  [gbastien]
- Added possibility to restrict suffixes to only some selected organizations.
  Plone groups will only be created for selected organizations.  When selecting or
  unselecting organizations, linked Plone groups are created/deleted accordingly.
  [gbastien]
- Moved setting.getOwnOrganizationPath to
  utils.get_own_organization/utils.get_own_organization_path.
  [gbastien]
- Added method utils.get_plone_groups that returns every Plone groups of a
  given organization.
  [gbastien]
- Added utils.get_plone_group that returns a Plone group for given organization
  UID and suffix.
  [gbastien]
- Disabled auto_append on IContactPlonegroupConfig.functions DataGridField.
  [gbastien]
- Notify event PlonegroupGroupCreatedEvent when a Plone group linked to an
  organization is created.
  [gbastien]
- z3c.table batching does not work when displaying suborganizations, so set
  batchSize and startBatchingAt to 999 instead 200 so we are pretty sure it is
  never displayed.
  [gbastien]
- While displaying "@@suborganizations", display a specific message "No suborganization"
  when no suborganizations instead displaying nothing.
  [gbastien]
- Added default logger importable from collective.contact.plonegroup.
  [gbastien]
- Added utils.select_organization to be able to select or unselect an
  organization from organizations registry.
  [gbastien]
- While creating Plone groups, translate suffix displayed in title.
  [gbastien]

1.9 (2018-09-04)
----------------

- Added utils.get_plone_group_id to get Plone group id for given organization and suffix.
  [gbastien]
- Overrided "@@suborganizations" view to display the entire hierarchy of contained
  organizations and sub-organizations and more informations in a table.
  [gbastien]
- When the plonegroup-organization is displayed in a tooltip, use original way
  to display sub organizations because the new rendering using the table takes
  too much place in the tooltip.
  [gbastien]

1.8.1 (2018-07-30)
------------------

- Sort user vocabulary by fullname
  [sgeulette]
- Added cache on travis.
  [sgeulette]

1.8 (2017-09-18)
----------------

- Corrected error when deleting site.
  [sgeulette]
- Corrected group modification. Added migration step.
  [sgeulette]

1.7 (2017-07-25)
----------------

- Check if linkintegrity is enabled in events.
  [sgeulette]

1.6 (2017-05-30)
----------------

- Use manager role only if necessary to avoid "SystemError: Excessive recursion" when recataloging
  [sgeulette]
- Protect against group deletion
  [sgeulette]
- Corrected subscriber at object paste
  [sgeulette]

1.5 (2016-12-13)
----------------

- Get selected organizations with manager role because plone.formwidget.masterselect calls ++widget++ as Anonymous.
  [sgeulette]

1.4 (2016-12-07)
----------------

- Call only once a subscriber.
  [sgeulette]
- Improved util method and added test
  [sgeulette]
- Added method to get selected organizations with customized title
  [sgeulette]
- Added methods to get orgs users and vocabulary
  [sgeulette]

1.3 (2016-04-15)
----------------

- Use a stored cache key to invalidate cache on all zeo clients
  [sgeulette]

1.2 (2016-01-13)
----------------

- Made an unrestricted search to list own organizations, possible reason of empty list
  [sgeulette]
- Increase OrderedSelectWidget size to 15 lines.
  [sgeulette]
- Use the same permission to protect config view and configlet.
  [sgeulette]

1.1 (2015-12-11)
----------------

- Put title as unicode in vocabulary.
  [sgeulette]

1.0 (2015-11-24)
----------------

- Added link integrity check when deleting a plonegroup organization
  [sgeulette]
- Added marker interfaces to distinguish plonegroup organizations
  [sgeulette]
- Added selected organizations vocabulary as elephantvocabulary: display correctly no more selected terms.
  [sgeulette]
- Don't deactivate a used plonegroup organization
  [sgeulette]
- Check state to build OwnOrganizationServicesVocabulary.
  [cedricmessiant]
- Set token to UID in OwnOrganizationServicesVocabulary.
  [sgeulette]
- Give access to configlet to Site Administrator
  [sgeulette]
- Flake8 corrections
  [sgeulette]


0.2 (2014-03-18)
----------------

- Corrected Manifest to include all files.


0.1 (2014-02-13)
----------------

- Initial release.
  [sgeulette]
