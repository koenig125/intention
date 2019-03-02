$(document).ready(function() {
    $(".task").click(function(e) {
        if($(this).hasClass('selected')){
            $(this).removeClass('selected');
        } else {
            $(this).addClass("selected");
        }
    });
});
