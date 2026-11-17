*** Settings ***
Documentation  Plone 6 Classic UI keywords. Same keyword names and arguments as ui_plone4.robot.
...            Robot Framework 3.2 syntax: shared with the Plone 4.3 (Python 2) environment.
...            Datagridfield: pat-datagridfield; tooltips: tooltipster (collective.contact.core forms.js).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote


*** Variables ***
${ERROR_PAGE_TEXT}  there seems to be an error


*** Keywords ***
Log in with the login form
    [Documentation]  Real login (creates the user folder), unlike autologin
    [Arguments]  ${username}  ${password}
    Disable autologin
    Go to  ${PLONE_URL}/login
    Input text  css=#__ac_name  ${username}
    Input password  css=#__ac_password  ${password}
    Click button  css=#buttons-login
    Wait until page contains element  css=#personaltools-menulink

Do the workflow transition
    [Documentation]  Item of the workflow menu, by transition id
    [Arguments]  ${transition_id}
    Click element  css=#plone-contentmenu-workflow > a
    Wait until element is visible  css=#workflow-transition-${transition_id}
    Click element  css=#workflow-transition-${transition_id}

The status message contains
    [Arguments]  ${text}
    Wait until element contains  css=.portalMessage  ${text}

The page is not an error
    Page should not contain  ${ERROR_PAGE_TEXT}

Add a datagridfield row after
    [Documentation]  Insert button of a row (by index) of a datagridfield (by widget id)
    [Arguments]  ${widget_id}  ${index}
    Click button  css=#${widget_id} tr[data-index="${index}"] .dgf--row-add

The tooltip shows the organization
    [Documentation]  Tooltip opened by hovering a .link-tooltip link: the organization view (title), not the whole page
    [Arguments]  ${full_title}
    Wait until element contains  css=.tooltipster-base h1  ${full_title}  timeout=10s
    Page should not contain element  css=.tooltipster-base #portal-header
