$(document).ready(function(){
    $('.subsection-plonegroup-organization .portalMessage.error dd').html(function(index, html){
        // returns interpreted string with entities replaced
        return $("<div/>").html(html).text();
    });
})
