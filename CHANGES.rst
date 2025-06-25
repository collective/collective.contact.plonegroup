Changelog
=========

1.54 (2025-06-25)
-----------------

- Set `toggle_parent_active=true` when calling JS `toggleDetails` for opening
  an organization linked users and groups so the `[+]` turns to `[-]`.
  [gbastien]

1.53 (2025-05-05)
-----------------

- Corrected bugs in `settings.validateSettings`.
  [sgeulette]
- Include user email in addition to id in `@@display-group-users`
  so we have `Fullname (user_id, user@email)` for `Managers`.
  [gbastien]

1.52 (2025-02-06)
-----------------

- Added parameter `verify_group_exist=True` to `utils.get_plone_groups`.
  When set to `False`, it will not get the real Plone group object to check
  if it exist when using `ids_only=True`. In this case it is much faster.
  [gbastien]

1.51 (2024-10-02)
-----------------

- Added helpers `utils.enable_function` and `utils.disable_function`
  to easily enable/disable a function.
  [gbastien]

1.50 (2024-05-27)
-----------------

- Fixed `DisplayGroupUsersView.group_title` when `DisplayGroupUsersView.short=True`
  and group title contains several parenthesis.
  [gbastien]

1.49 (2024-04-10)
-----------------

- Corrected behavior zcml definition to avoid message when Plone starts.
  [sgeulette]
- Import `safe_encode` from `imio.pyutils` instead `imio.helpers`.
  [gbastien]

1.48 (2024-02-19)
-----------------

- Added `behaviors.IPlonegroupUserLink` with userid and primary_organization fields.
  [sgeulette]
- Added `utils.get_person_from_userid` and `utils.get_persons_from_userid`
  [sgeulette]

1.47 (2023-10-19)
-----------------

- Fixed typo in french translation.
  [gbastien]

1.46 (2023-07-07)
-----------------

- Added parameter `omitted_suffixes=[]` to `utils.get_all_suffixes`.
  [gbastien]

1.45 (2023-02-27)
-----------------

- Avoid useless variable initialization in `utils.get_plone_group`,
  do everything in one line.
  [gbastien]

1.44 (2022-08-19)
-----------------

- Warning, changed behavior of `utils.get_organization`, added parameter
  `only_in_own_org=True` that will make sure that given `org_uid` is an
  organization inside own organization.
  [gbastien ]
- Added `get_selected_org_suffix_principal_ids` and `voc_selected_org_suffix_userids`
  to work only with group and user ids
  [sgeulette]
- Used cached method `get_users_in_plone_groups` from imio.helpers
  [sgeulette]

1.43 (2022-07-01)
-----------------

- Added `utils.get_suffixed_groups`.
  [sgeulette]
- Do not delete a group (after a function removal) if not empty
  [sgeulette]

1.42 (2022-06-14)
-----------------

- Escape user and group title in `DisplayGroupUsersView`.
  Moreover fixed column to be not sortable.
  [gbastien]
- Added `safe_utils.py` that will only include safe utils.
  [gbastien]
- Corrected error in search: do not pass empty portal_type criteria.
  [sgeulette]
- Added parameter escaped=True in `voc_selected_org_suffix_users` function
  [sgeulette]
- Fixed `@@display-group-users` when organization is not selected in plonegroup
  so there is no linked Plone groups, added tests for it and the
  `@@suborganizations` view (z3ctable displaying organizations contained in
  another organization).
  [gbastien]

1.41 (2022-05-06)
-----------------

- Added adapter with methods to check PloneGroupContact delete and transition.
  [sgeulette]

1.40 (2022-04-22)
-----------------

- Adapted the `PloneGroupUsersGroupsColumn` to display linked group also when
  organization is not selected in plonegroup, this lets display linked Plone groups
  of an organization that was selected then unselected.
  [gbastien]

1.39 (2022-02-03)
-----------------

- Distinguished cached calls in vocabularies.
  [sgeulette]

1.38 (2021-11-26)
-----------------

- In `utils.get_organization` and `utils.get_organizations`, query catalog unrestricted.
  [gbastien]
- Removed `uuidToObject` imported from `plone.app.uuid` in `settings.py`,
  we use `uuidToObject` from `imio.helpers`.
  [gbastien]

1.37 (2021-10-20)
-----------------

- Corrected cache invalidation bug, that wasn't done when a previously deactivated
  organisation is reactivated. Invalidate now wider.
  [sgeulette]

1.36 (2021-08-27)
-----------------

- Added logging using `collective.fingerpointing` in the
  `@@manage-own-groups-users` view when a user was added or removed.
  [gbastien]
- Added `available_expr` to the action displaying the `Manage own groups`,
  action will be displayed if at least one value is selected in the
  `groups_management` field in the configuration.
  [gbastien]
- Use `imio.helpers.SortedUsers` vocabulary in the
  `@@manage-own-groups-users` view.
  [gbastien]

1.35 (2021-05-05)
-----------------

- Fixed `addOrModifyOrganizationGroups` called when an organization is modified,
  that was creating Plone groups for every suffixes without considering
  `enabled` or `fct_orgs`. Added upgrade step to `v8` that will delete Plone
  groups that were wrongly created.
  [gbastien]

1.34 (2021-04-20)
-----------------

- Fixed `settings.detectContactPlonegroupChange` where sometimes `event.oldValue`
  is None when value is set several times from different testing layers.
  [gbastien]

1.33 (2021-01-06)
-----------------

- Do not grok the package anymore.
  [gbastien]
- Override vocabulary `PositionTypes` from `collective.contact.core`, when
  `context` out of a directory, get `position_types` from `DEFAULT_DIRECTORY_ID`.
  [gbastien]

1.32 (2020-10-26)
-----------------

- Fixed `DisplayGroupUsersView.group_title` when `DisplayGroupUsersView.short=True`
  to only apply if we have a format like `My config (My suffix)` or it removed
  last letter.
  [gbastien]
- Added parameter `PloneGroupUsersGroupsColumn.short=True` so
  `@@display-group-users` is rendered short by default.
  [gbastien]

1.31 (2020-10-11)
-----------------

- Combined v6 and v7 upgrade because it fails coming from v5
  [sgeulette]
- Corrected table class name.
  [sgeulette]

1.30 (2020-10-02)
-----------------

- Added manage-own-groups-users view and functions/groups selection configuration.
  A user can manage the user assignments of his groups.
  [sgeulette]
- Avoid getting groups (only users) in `get_selected_org_suffix_users` function.
  [sgeulette]
- Avoid GroupNotFoundError in `get_selected_org_suffix_users` if suffix is limited to some organizations.
  [sgeulette]
- Added `BaseOrganizationServicesVocabulary._term_value` and
  `BaseOrganizationServicesVocabulary._term_token` to ease override
  of rendered term value and token.
  [gbastien]
- Make `SelectedOrganizationsElephantVocabulary` inherits from
  `OwnOrganizationServicesVocabulary` so methods `_term_value` and
  `_term_token` are available.
  [gbastien]
- In `@@display-group-users` instead displaying contained groups without
  contained members, display members of contained groups for normal users,
  display contained groups and contained members to Managers.
  [gbastien]
- Fixed `ConnectionStateError` while setting `registry[FUNCTIONS_REGISTRY]`
  in tests and profile is applied several times.
  [gbastien]

1.29.1 (2020-08-26)
-------------------

- Fix CSS for `@@display-group-users` view when current user not a Manager
  and so does not have link on prefixed icon (user/group).
  [gbastien]

1.29 (2020-08-18)
-----------------

- Added `PloneGroupUsersGroupsColumn`, a column that displays suffixed groups
  and users, to be called on dashboard displaying organizations.
  The groups and users are rendered by the `@@display-group-users` view
  that may also be used outside.
  By default, as groups and users may be very long to display, it is hidden
  in a collapsible `<div>` and displayed asynchronously.
  [gbastien]
- Added possibility to disable a `function` (`enabled=True` by default),
  this is useful to avoid deleting a `function` and re-adding it after,
  sometimes faultly.  Adapted `utils.get_all_suffixes(only_enabled=True)`
  to only get enabled functions.
  Added upgrade step to version `6` to manage new value `enabled=True`
  in `functions` stored in the `regsitry`.
  [gbastien]
- Remove item `UID` from link in `OrgaPrettyLinkWithAdditionalInfosColumn`
  as it is now displayed as additional information by default.
  [gbastien]

1.28 (2020-05-26)
-----------------

- In `utils.get_organizations`, do not use a `list comprehension` to turn
  result of `get_registry_organizations` into a list as it is already the case
  (was not the case a long time ago), `get_registry_organizations` returns a
  new list and values stored in the registry will not be changed anymore by
  default.
  [gbastien]

1.27 (2020-05-08)
-----------------

- Make the `OrgaPrettyLinkWithAdditionalInfosColumn` also work for `person` and `held_position`.
  [gbastien]

1.26 (2020-03-12)
-----------------

- As vocabulary `ram.cache` cachekey are generated based on
  module/class names, renamed vocabularies
  `collective.contact.plonegroup.selected_organization_services` to
  `collective.contact.plonegroup.browser.settings.SelectedOrganizationsElephantVocabulary`
  and `collective.contact.plonegroup.sorted_selected_organization_services` to
  `collective.contact.plonegroup.browser.settings.SortedSelectedOrganizationsElephantVocabulary`.
  Added tests showing that cache is correctly invalidated when selected organizations changed.
  [gbastien]

1.25 (2020-02-06)
-----------------

- Use `collective.contact.plonegroup.sorted_selected_organization_services`
  for `settings.IFunctionSchema.fct_orgs`
  (field for restricting a suffix to some organizations).
  [gbastien]
- In `validateSettings` invariant check if Plone group is empty using
  `getGroupMembers` that ignores `<not found>` users instead `getMemberIds`.
  [gbastien]

1.24 (2019-11-25)
-----------------

- Added group_as_str param in organizations_with_suffixes function.
  [sgeulette]

1.23 (2019-11-04)
-----------------

- Added parameter `caching=True` to `utils.get_organization`, this will store
  the organization object in the REQUEST and avoid too much catalog queries.
  [gbastien]

1.22 (2019-09-26)
-----------------

- When passing `kept_org_uids` to `utils.get_organizations`,
  make sure order is preserved.
  [gbastien]

1.21 (2019-09-13)
-----------------

- Added `BaseOrganizationServicesVocabulary._term_title` to ease override of
  rendered term title.
  [gbastien]

1.20 (2019-09-12)
-----------------

- Added `collective.contact.plonegroup.every_organizations` vocabulary, to do
  this needed to write `BaseOrganizationServicesVocabulary` from which
  `OwnOrganizationServicesVocabulary` and `EveryOrganizationsVocabulary`
  inherits.
  [gbastien]
- Removed sorting on term title for
  `collective.contact.plonegroup.selected_organization_services`, terms are
  displayed following selection order in plonegroup organizations like before.
  Added new vocabulary sorted on term title and available as
  `collective.contact.plonegroup.sorted_selected_organization_services`.
  [gbastien]

1.19 (2019-08-23)
-----------------

- Optimized `OwnOrganizationServicesVocabulary.listSubOrganizations`, do the
  catalog query only if current organization contains something.
  [gbastien]

1.18 (2019-08-02)
-----------------

- In `OrgaPrettyLinkWithAdditionalInfosColumn`, set `showContentIcon` to True
  and enable `link-tooltip`.
  [gbastien]
- In `SelectedInPlonegroupColumn`, display `Not` in bold.
  [gbastien]
- Added `collective.contact.plonegroup.functions` vocabulary listing every
  functions defined in plonegroup control panel.
  [gbastien]

1.17 (2019-07-15)
-----------------

- Corrected bad full title shortening.
  [sgeulette]

1.16 (2019-06-30)
-----------------

- Fixed error in `OrgaPrettyLinkWithAdditionalInfosColumn` when displaying
  organizations out of `PLONEGROUP_ORG`.
  [gbastien]
- Fixed `utils.get_organizations` when `caching=True` to store a new list of
  organizations in the cache instead returned value or value in cache may be
  modified if we modify returned value in a sub method...
  [gbastien]
- Use `get_registry_organizations/set_registry_organizations` and
  `get_registry_functions/set_registry_functions` as much as possible.
  [gbastien]

1.15 (2019-06-07)
-----------------

- Fixed problem, linked Plone groups title were not updated when suffix title
  changed and some `fct_orgs` were defined.
  [gbastien]
- In `settings.detectContactPlonegroupChange`, set `changes = True` only when
  relevant, due to wrong indentation, it was done systematically.
  [gbastien]

1.14 (2019-05-16)
-----------------

- Make `OrgaPrettyLinkWithAdditionalInfosColumn` work if displaying the
  `plonegroup-organization`, include link to plonegroup configuration panel in
  `SelectedInPlonegroupColumn` header.
  [gbastien]
- Changed first parameter name for `utils.get_plone_group` and
  `utils.get_plone_group_id` from `org_uid` to `prefix` as it can be used in
  other cases.
  [gbastien]
- Added helper method `utils.select_org_for_function` to be able to add/remove
  an organization uid from `fct_orgs` defined on a `function`.
  [gbastien]
- Removed dependency on `unittest2`.
  [gbastien]
- When calling `config.get_registry_organizations` and
  `config.get_registry_functions`, by default return a copy of stored data to
  avoid changing it.
  [gbastien]
- Added parameter `default=True` to `utils.get_own_organization`, in this case,
  default ids for `root directory` and `own organization` are used instead
  using a catalog query, it should be faster.
  [gbastien]

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
