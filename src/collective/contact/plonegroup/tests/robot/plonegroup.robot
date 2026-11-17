*** Settings ***
Documentation  collective.contact.plonegroup keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.2 syntax (shared with the Plone 4.3 environment).
...            Fixture: testing.AcceptanceLayer (My organization with Department 1 (selected) and Department 2,
...            'director' function, 'investigators' group, Members chef (in both) and agent).
Resource  ui_plone${PLONE_MAJOR}.robot


*** Variables ***
${OWN_ORGANIZATION}  ${PLONE_URL}/contacts/plonegroup-organization
${DEPARTMENT1}  ${OWN_ORGANIZATION}/department1
${DEPARTMENT2}  ${OWN_ORGANIZATION}/department2
${SETTINGS_URL}  ${PLONE_URL}/@@contact-plonegroup-settings
${OWN_GROUPS_URL}  ${PLONE_URL}/@@manage-own-groups-users


*** Keywords ***
Open a manager browser
    Open test browser
    Set window size  1280  2000
    Enable autologin as  Manager

Open a group manager browser
    [Documentation]  chef, a Member in the manageable 'investigators' group and Department 1 'director' group
    Open test browser
    Set window size  1280  2000
    Log in with the login form  chef  chefpassword

The settings form is shown
    Wait until page contains element  css=#form-widgets-functions
    The page is not an error
    Element should contain  css=#form-widgets-organizations-to  Department 1

Select in the ordered selection
    [Documentation]  Move an option (by label) to the selected list of an ordered selection widget (by widget id)
    [Arguments]  ${widget_id}  ${label}
    Select from list by label  css=#${widget_id}-from  ${label}
    Click button  css=#${widget_id} button[name="from2toButton"]

Sub-organization row
    [Documentation]  Locator of the row of a sub-organization (by title) in the @@suborganizations table
    [Arguments]  ${title}
    [Return]  xpath=//table[contains(@class, "suborganizations-listing")]/tbody/tr[./td/a[contains(@class, "pretty_link")][normalize-space(.)="${title}"]]

The sub-organization link opens in a new window
    [Arguments]  ${title}  ${url}
    ${row}=  Sub-organization row  ${title}
    Element attribute value should be  ${row}/td/a[contains(@class, "pretty_link")]  href  ${url}
    Element attribute value should be  ${row}/td/a[contains(@class, "pretty_link")]  target  _blank

The sub-organization is selected in plonegroup
    [Documentation]  "Selected in plonegroup" cell: Yes, or No in red bold (css class)
    [Arguments]  ${title}  ${expected}=${True}
    ${row}=  Sub-organization row  ${title}
    ${value}=  Set variable if  ${expected}  true  false
    Page should contain element  ${row}/td[contains(@class, "bool_value_${value}")]

Show the group users of the sub-organization
    [Documentation]  Click "Details" in the "Groups and users" column
    [Arguments]  ${title}
    ${row}=  Sub-organization row  ${title}
    Click element  ${row}//div[contains(@class, "collapsible")][not(contains(@class, "collapsible-content"))]

The group users of the sub-organization contain
    [Arguments]  ${title}  ${text}
    ${row}=  Sub-organization row  ${title}
    Wait until element contains  ${row}//div[contains(@class, "collapsible-content")]  ${text}

Hover the sub-organization link
    [Arguments]  ${title}
    ${row}=  Sub-organization row  ${title}
    Mouse over  ${row}/td/a[contains(@class, "pretty_link")]

Add an assignment
    [Documentation]  Own groups form: choose the group in the blue (auto-append) line of a datagrid (by widget id),
    ...              then the user in the line it became (brown, new-row)
    [Arguments]  ${widget_id}  ${group}  ${user}
    Select from list by label  css=#${widget_id} tr.auto-append select[id$="-widgets-group"]  ${group}
    Wait until page contains element  css=#${widget_id} tr.new-row select[id$="-widgets-user"]
    Select from list by label  css=#${widget_id} tr.new-row select[id$="-widgets-user"]  ${user}

The assignment is listed
    [Arguments]  ${widget_id}  ${group}  ${user}
    Page should contain element  xpath=//table[@id="${widget_id}"]//tr[.//select[contains(@id, "-widgets-group")]/option[@selected][normalize-space(.)="${group}"]][.//select[contains(@id, "-widgets-user")]/option[@selected][normalize-space(.)="${user}"]]

The assignment is locked
    [Documentation]  An existing row (by index) keeps its values: the other options are disabled
    [Arguments]  ${widget_id}  ${index}  ${user}
    List selection should be  css=#${widget_id}-${index}-widgets-user  ${user}
    Page should contain element  css=#${widget_id}-${index}-widgets-user option[disabled]
    Page should not contain element  css=#${widget_id}-${index}-widgets-user option:not([disabled]):not([selected])
