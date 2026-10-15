*** Settings ***
Documentation  A plonegroup organization used in the configuration or by content is protected.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  plonegroup.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
The delete confirmation of a used organization lists the content using it
    Go to  ${DEPARTMENT2}/delete_confirmation
    Page should contain  Potential link breakage
    Page should contain element  xpath=//*[@id="content"]//li/a[normalize-space(.)="Content of department 2"]

Deactivating a selected organization is refused
    Go to  ${DEPARTMENT1}
    Do the workflow transition  deactivate
    The status message contains  You cannot deactivate this item !
    Page should contain  This contact is selected in configuration
