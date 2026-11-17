*** Settings ***
Documentation  @@suborganizations table of a plonegroup organization.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  plonegroup.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
The sub-organizations are listed with their plonegroup selection
    Go to  ${OWN_ORGANIZATION}
    The page is not an error
    Page should contain element  css=#content a[href="${SETTINGS_URL}"]
    The sub-organization link opens in a new window  Department 1  ${DEPARTMENT1}
    The sub-organization link opens in a new window  Department 2  ${DEPARTMENT2}
    The sub-organization is selected in plonegroup  Department 1
    The sub-organization is selected in plonegroup  Department 2  ${False}

Details shows the users of the groups of a sub-organization
    Go to  ${OWN_ORGANIZATION}
    Show the group users of the sub-organization  Department 1
    The group users of the sub-organization contain  Department 1  Director
    The group users of the sub-organization contain  Department 1  Chef Boss

Hovering a sub-organization link shows that organization in a tooltip
    Go to  ${OWN_ORGANIZATION}
    Hover the sub-organization link  Department 2
    The tooltip shows the organization  My organization / Department 2
