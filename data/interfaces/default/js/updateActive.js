"use strict";

function append_to_dom(data) {
    var data = JSON.parse(data)
    if (data.length == 0) {
        return
    }
    document.getElementById("activeProgress").innerHTML = data.progress;
}

function doPoll() {
    $.ajax({
        url: "update"
    }).done(function (data) {
        append_to_dom(data);
    }).always(function () {
        setTimeout(doPoll, 1000);
    })
}