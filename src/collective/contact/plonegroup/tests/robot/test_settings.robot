*** Settings ***
Documentation  Contact Plone Group settings (control panel).
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  plonegroup.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
The settings are reachable from the site setup
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link  css=ul.configlets a[href="${SETTINGS_URL}"]
    The settings form is shown

Adding a function creates the Plone groups of the selected organizations
    Go to  ${SETTINGS_URL}
    The settings form is shown
    Add a datagridfield row after  form-widgets-functions  0
    Input text  css=#form-widgets-functions-1-widgets-fct_id  observer
    Input text  css=#form-widgets-functions-1-widgets-fct_title  Observers
    # the organizations of a new row are chosen once the server renders it: the ordered selection buttons
    # of a row added by javascript still target the template row (Plone 4, organizations required there)
    Click button  css=#form-buttons-save
    Select in the ordered selection  form-widgets-functions-1-widgets-fct_orgs  Department 1
    Click button  css=#form-buttons-save
    The status message contains  Changes saved
    Go to  ${PLONE_URL}/@@usergroup-groupprefs
    Page should contain  Department 1 (Observers)
