$(document).ready(function(){
    $('.subsection-plonegroup-organization .portalMessage.error dd').html(function(index, html){
        // returns interpreted string with entities replaced
        return $("<div/>").html(html).text();
    });
    $("body.template-manage-own-groups-users table.datagridwidget-table-view :not(.auto-append):not(.new-row):not(.datagridwidget-empty-row).datagridwidget-row option:not([selected])").attr("disabled", "disabled");
})

var handleDGFAfterAuto = function(event, dgf, row) {
    row = $(row);
    parents=row.parents('table.datagridwidget-table-view');
    $('#' + parents[0].id + ' tr.datagridwidget-row.row-' + row.data('index')).addClass('new-row');
};

// Bind all DGF handlers on the page
$(document).on('afteraddrowauto', 'body.template-manage-own-groups-users table.datagridwidget-table-view', handleDGFAfterAuto);
