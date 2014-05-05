var refresh_gui = true;
var editor = null;
var series_data = []

// READY
$(function() {
    initialize_editor();
    initialize_hourly_demands();
    $.getJSON("/api/status/", function(data) {
        if (data['system'] == 'init') {
            initialize_wizard();
        } else {
            initialize_diagram();
        }
    }).done(function() {
        // $.getJSON("/api/code/", function(data) {
        //     editor.setValue(data['editor_code'], 1);
        // });
    });

    initialize_event_handlers();
});

// INITIALIZATIONS
function initialize_editor() {
    ace.require("ace/ext/language_tools");
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/github");
    editor.getSession().setMode("ace/mode/python");
    editor.setOptions({
        enableBasicAutocompletion: true,
        enableSnippets: true
    });
    ace.config.loadModule('ace/snippets/snippets', function() {
        var snippetManager = ace.require('ace/snippets').snippetManager;
        ace.config.loadModule('ace/snippets/python', function(m) {
            if (m) {
                m.snippets = m.snippets.concat(custom_snippets);
                snippetManager.register(m.snippets, m.scope);
            }
        });
    });
}

function initialize_hourly_demands() {
    for (var i = 0; i < 24; i++) {
        $("#daily_thermal_demand").append("<span id='daily_thermal_demand_" + i + "' class='slider_thermal'><span>" + i + "</span></span>");
        $("#daily_electrical_variation").append("<span id='daily_electrical_variation_" + i + "' class='slider_electrical'><span>" + i + "</span></span>");
    }

    $(".slider_thermal").slider({
        value: 0,
        min: 0,
        max: 3000,
        range: "min",
        animate: true,
        orientation: "vertical",
        slide: function(event, ui) {
            var text = "(Current value: " + ui.value / 100 + "C)";
            $("#daily_thermal_demand_info").text(text);
        },
        stop: function(event, ui) {
            $("#daily_thermal_demand_info").text('');
        }
    });

    $(".slider_electrical").slider({
        value: 0,
        min: 0,
        max: 20000,
        range: "min",
        animate: true,
        orientation: "vertical",
        slide: function(event, ui) {
            var text = "(Current value: " + ui.value / 100 + "%)";
            $("#daily_electrical_variation_info").text(text);
        },
        stop: function(event, ui) {
            $("#daily_electrical_variation_info").text('');
        }
    });
}

function initialize_event_handlers() {
    $("#settings").submit(function(event) {
        var post_data = $("#settings").serialize();
        for (var i = 0; i < 24; i++) {
            post_data += "&daily_thermal_demand_" + i + "=" + ($("#daily_thermal_demand_" + i).slider("value") / 100);
        }
        for (var i = 0; i < 24; i++) {
            post_data += "&daily_electrical_variation_" + i + "=" + ($("#daily_electrical_variation_" + i).slider("value") / 10000);
        }
        $.post("/api/settings/", post_data, function(data) {
            $("#settings_button").removeClass("btn-primary");
            $("#settings_button").addClass("btn-success");
            update_setting(data);
            setTimeout(function() {
                $("#settings_button").removeClass("btn-success");
                $("#settings_button").addClass("btn-primary");
                hide_forecasts();
            }, 500);
        });
        event.preventDefault();
    });

    $("#settings").change(function() {
        immediate_feedback();
    });

    $("#settings_simulate_button").click(function( event ) {
        event.preventDefault();
        immediate_feedback();
    });

    

    $(".fast_forward_button").click(function(event) {
        $.post("/api/simulation/", {
            forward: $(this).val()
        });
    });

    $("#editor_button").click(function() {
        $.post("/api/settings/", {
            code: editor.getValue(),
            password: $('#password').val()
        }, function(data) {
            hide_forecasts();
            editor.setValue(data['editor_code'], 1);
        });
    });

    $("#editor_simulate_button").click(function( event ) {
        event.preventDefault();
        $.post("/api/forecasts/", {
            code: editor.getValue(),
            password: $('#password').val(),
            forecast_time: 3600.0 * 24 * 30
        }, function(data) {
            update_forecast(data, true);
        });
    });

    $("#pause_refresh").click(function(event) {
        refresh_gui = !refresh_gui;
        if (refresh_gui) {
            $("#pause_refresh span").removeClass('glyphicon-pause');
            $("#pause_refresh span").addClass('glyphicon-refresh');
        } else {
            $("#pause_refresh span").removeClass('glyphicon-refresh');
            $("#pause_refresh span").addClass('glyphicon-pause');

        }
        event.preventDefault();
    });

    $("#reset_simulation").click(function(event) {
        $.post("/api/simulation/", {
            reset: 1
        });
        // location.reload(true);
    });

    $("#save_snippet").submit(function(event) {
        $.post("/api/code/", {
            save_snippet: $("#snippet_name").val(),
            code: editor.getValue()
        }, function(data) {
            editor.setValue(data['editor_code'], 1);

            // refresh snippet list
            if ('code_snippets' in data) {
                $("#snippets").html('');
                $.each(data['code_snippets'], function(index, snippet_name) {
                    $("#snippets").append('<option>' + snippet_name + '</option>');
                });
            }
        });
        event.preventDefault();
    });

    $("#load_snippet").submit(function(event) {
        $.post("/api/code/", {
            snippet: $("#snippets").val()
        }, function(data) {
            editor.setValue(data['editor_code'], 1);
        });
        event.preventDefault();
    });

    $("#export_data").submit(function(event) {
        $.post("/api/simulation/", {
            export: $("#export_name").val()
        });
        event.preventDefault();
    });
}

function initialize_diagram() {
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    $.getJSON('/api/sensors/', function(data) {
        $.each(data, function(index, value) {
            series_data.push({
                name: value.name + ' (Device #' + value.device_id + ')',
                data: [],
                color: colors_past[index],
                tooltip: {
                    valueSuffix: ' ' + value.unit
                }
            });
            series_data.push({
                name: value.name + ' (Device #' + value.device_id + ' predicted)',
                data: [],
                color: colors_future[index],
                dashStyle: 'shortdot',
                tooltip: {
                    valueSuffix: ' ' + value.unit
                }
            });
        });

        // Create the chart
        $('#simulation_diagram').highcharts('StockChart', {
            chart: {
                height: 400,
                zoomType: 'xy',
                events: {
                    load: refresh
                }
            },
            rangeSelector: {
                buttons: [{
                    count: 6,
                    type: 'hour',
                    text: '6H'
                }, {
                    count: 12,
                    type: 'hour',
                    text: '12H'
                }, {
                    count: 1,
                    type: 'day',
                    text: '1D'
                }, {
                    count: 1,
                    type: 'week',
                    text: '1W'
                }, {
                    count: 2,
                    type: 'week',
                    text: '2W'
                }, {
                    count: 1,
                    type: 'month',
                    text: '1M'
                }, {
                    count: 2,
                    type: 'month',
                    text: '2M'
                }, {
                    count: 3,
                    type: 'month',
                    text: '3M'
                }, {
                    count: 6,
                    type: 'month',
                    text: '6M'
                }, {
                    count: 9,
                    type: 'month',
                    text: '9M'
                }, {
                    type: 'all',
                    text: 'All'
                }],
                selected: 6,
                inputEnabled: false
            },
            xAxis: {
                plotLines: [{
                    value: 0,
                    width: 2,
                    color: 'red',
                    label: {
                        text: 'Now',
                        align: 'right',
                        y: 32,
                        x: 6
                    }
                }]
            },
            tooltip: {
                valueDecimals: 2
            },
            lang: {
                noData: "Loading data..."
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: false
                    },
                    lineWidth: 1.5,
                }
            },
            series: series_data,
            credits: {
                enabled: false
            }
        });
        initialize_diagram_filters();
    });

}

function initialize_diagram_filters() {
    for (var i = 0; i < 7; i++) {
        series = series_data[i];
        $('#diagram_filters').append('<label class="btn btn-default" style="color: ' + series.color + ';"><input class="btn diagram_filter" type="checkbox" value="' + i + '">' + series.name + '</label>');
    };

    $('.diagram_filter').change(filter_series);

}

function initialize_wizard(show) {
    // $.fn.wizard.logging = true;
    var options = {
        submitUrl: '/api/configure/',
        contentWidth: 1000,
        contentHeight: 500,
        showCancel: false,
        showClose: false,
        buttons: {
            submitText: 'Configure',
            submittingText: "Configuring..."
        }
    };
    var wizard = $("#startup").wizard(options);
    wizard.show();

    wizard.on('submit', function(wizard) {
        var post_data = wizard.serializeArray();
        for (var i = 0; i < post_data.length; i++) {
            var input = $('[name="' + post_data[i].name + '"]');
            post_data[i]['device_id'] = input.attr('data-device');
            post_data[i]['key'] = input.attr('data-key');
            post_data[i]['type'] = input.attr('data-type');
            post_data[i]['unit'] = input.attr('data-unit');
        };

        $.ajax({
            type: "POST",
            contentType: 'application/json',
            url: wizard.args.submitUrl,
            data: JSON.stringify(post_data),
            dataType: "json"
        }).done(function(response) {
            initialize_diagram();
            wizard.submitSuccess();
            wizard.close();
        }).fail(function() {
            wizard.submitFailure();
            wizard.hideButtons();
        });
        $.getJSON("/api/settings/", function(data) {
            update_setting(data);
        });
    });
}