var api_url = "http://www.hpi.uni-potsdam.de/hirschfeld/bachelorprojects/2013H1/api/";

var device_id = null;
var range_start = new Date().getTime()-24*60*60*1000;
var range_end = new Date().getTime();

$(document).ready(function(){
    $("#login_submit").click(function(event) {
        hide_all();
        $('#login_box').modal('hide');
        $('#footer').fadeIn();
        $("#home").fadeIn();
    });

    $("#home_button").click(function(event) {
        hide_all();
        $("#home").fadeIn();
    });

    $("#settings_button").click(function(event) {
        hide_all();
        $("#settings").fadeIn();
    });

    $.get( api_url + "devices/", function( data ) {
      $.each(data, function(index, value){
        $("#device_list").append('<li class="device_items" id="device_item_' + value['id'] + '"><a onclick="show_device(' + value['id'] + ', \'' + value['name'] + '\');">' + value['name'] + '</a></li>');
      })
    });

    $("#range_slider").slider({
      range: true,
      min: -168,
      max: 0,
      values: [ -24, 0 ],
      slide: function( event, ui ) {
        if ( ui.values[0] >= ui.values[1] || (-ui.values[0]) + ui.values[1] > 72 ) {
            return false;
        }
        var start_date = new Date();
        start_date.setHours(start_date.getHours() + parseInt(ui.values[0]));
        var end_date = new Date();
        end_date.setHours(end_date.getHours() + parseInt(ui.values[1]));
        set_day_range(start_date, end_date);
      },
      change: function( event, ui ) {
        range_start = new Date().getTime()+60*60*1000*parseInt(ui.values[0]);
        range_end = new Date().getTime()+60*60*1000*parseInt(ui.values[1]);
        draw_diagram();
      }
    });

    set_day_range(new Date(range_start), new Date(range_end));

    $('#login_box').modal({
      backdrop: 'static'
    });

});

function show_device(id, device_name) {
    device_id = id;

    hide_all();
    $(".device_items").each(function () {
        $(this).removeClass('active');
    });

    $("#device_item_" + device_id).addClass('active');

    $("#devices").fadeIn();
    $("#device_name").text(device_name);

    draw_diagram();
}

function hide_all(){
    $("#home").hide();
    $("#devices").hide();
    $("#settings").hide();
}

function set_day_range(start, end){
    $( "#day_range" ).html( $.formatDateTime('dd.mm.yy hh:00', start) +
        " to " + $.formatDateTime('dd.mm.yy hh:00', end) );
}
