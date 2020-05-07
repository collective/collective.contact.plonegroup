$(document).ready(function(){
    $('.subsection-plonegroup-organization .portalMessage.error dd').html(function(index, html){
        // returns interpreted string with entities replaced
        return $("<div/>").html(html).text();
    });
    $("table.datagridwidget-table-view :not(.auto-append):not(.new-row):not(.datagridwidget-empty-row).datagridwidget-row option:not([selected])").attr("disabled", "disabled");
})

var handleDGFAfterAuto = function(event, dgf, row) {
    row = $(row);
    $('tr.datagridwidget-row.row-'+row.data('index')).addClass('new-row')
};

// Bind all DGF handlers on the page
$(document).on('afteraddrowauto', 'table.datagridwidget-table-view', handleDGFAfterAuto);
