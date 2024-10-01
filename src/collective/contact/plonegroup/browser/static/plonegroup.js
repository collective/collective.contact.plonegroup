$(document).ready(function(){

    $('.subsection-plonegroup-organization #global_statusmessage .portalMessage').html(function(index, html) {
        // returns interpreted string in portal messages with entities replaced
        $(this).contents().filter(function() {
            return this.nodeType === Node.TEXT_NODE;
        }).each(function() {
            var decodedHtml = $("<div>").html(this.nodeValue).text();
            $(this).replaceWith(decodedHtml);
        });
    });

    $("body.template-manage-own-groups-users .pat-datagridfield table :not(.auto-append):not(.new-row):not(.datagridwidget-empty-row).datagridwidget-row option:not([selected])").attr("disabled", "disabled");
})

var handleDGFAfterAuto = function(event, dgf, row) {
    added_row = $(row).prev();
    added_row.addClass('new-row');
};

// Bind all DGF handlers on the page
$(document).on('afteraddrow', 'body.template-manage-own-groups-users .pat-datagridfield', handleDGFAfterAuto);
