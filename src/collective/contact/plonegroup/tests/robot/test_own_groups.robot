*** Settings ***
Documentation  Own groups management (@@manage-own-groups-users) by a Member of manageable groups.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  plonegroup.robot
Test Setup  Open a group manager browser
Test Teardown  Close all browsers


*** Test Cases ***
A group manager adds a user to his group
    Go to  ${OWN_GROUPS_URL}
    Add an assignment  form-widgets-_groups_  Investigators  Agent Smith (agent)
    Click button  css=#form-buttons-apply
    The status message contains  Own groups users succesfully updated.
    The assignment is listed  form-widgets-_groups_  Investigators  Agent Smith (agent)
    The assignment is listed  form-widgets-_groups_  Investigators  Chef Boss (chef)

The existing assignments are locked
    Go to  ${OWN_GROUPS_URL}
    The assignment is locked  form-widgets-_groups_  0  Chef Boss (chef)
    The assignment is locked  form-widgets-director  0  Chef Boss (chef)
