
$(document).ready(function() {
    var selectedList;
    $(".task").click(function(e) {
        if($(this).hasClass('selected')){
            $(this).removeClass('selected');
            delete selectedList[selectedList.indexOf($(this).attr('id'))]
            console.log(selectedList);
        } else {
            $(this).addClass("selected");
            if(typeof selectedList == 'undefined'){
                selectedList = []
            }
            selectedList.push($(this).attr('id'))
            console.log(selectedList);
        }
    });

    $(".button").click(function(e) {
        var schedule;

        if(typeof selectedList == 'undefined'){
            selectedList = [];
        }else{
            selectedList = selectedList.filter(function (el) {
                return el != null;
            });
            console.log(selectedList);
        }

        if(this.id == 'today'){
            schedule = $("<input>").attr("type", "hidden")
            .attr("name", "schedule").val("TODAY");
        } else if (this.id == 'this_week') {
            schedule = $("<input>").attr("type", "hidden")
            .attr("name", "schedule").val("THIS_WEEK");
        } else {
            schedule = $("<input>").attr("type", "hidden")
            .attr("name", "schedule").val("NEXT_WEEK");
        }
        
        var selected = $("<input>").attr("type", "hidden")
        .attr("name", "mydata").val(selectedList);

        $('#task_form').append(schedule);
        $('#task_form').append(selected);
    
        $( "#task_form" ).submit()
    })

});
