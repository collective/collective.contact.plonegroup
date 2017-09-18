Changelog
=========


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
