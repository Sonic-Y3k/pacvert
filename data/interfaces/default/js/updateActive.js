"use strict";

function append_to_dom(data) {
    var parsedData = JSON.parse(data);
    if (parsedData.length === 0) {
        return;
    }
    
    var table = document.getElementById("to_process");
    if (table !== null) { //table element does exist
        for (var i = 1; i <= parsedData.length; i++) {
            var row = document.getElementById("process_row"+i);
            var cell0, cell1, cell2, cell3, cell4, cell5;
            if (row === null) {
                row = table.insertRow(i);
                row.id = "process_row" + i;
                
                cell0 = row.insertCell(0);
                cell1 = row.insertCell(1);
                cell2 = row.insertCell(2);
                cell3 = row.insertCell(3);
                cell4 = row.insertCell(4);
                cell5 = row.insertCell(5);
                
                cell0.id = "process_row"+i+"c0";
                cell1.id = "process_row"+i+"c1";
                cell2.id = "process_row"+i+"c2";
                cell3.id = "process_row"+i+"c3";
                cell4.id = "process_row"+i+"c4";
                cell5.id = "process_row"+i+"c5";
            } else {
                cell0 = document.getElementById("process_row"+i+"c0");
                cell1 = document.getElementById("process_row"+i+"c1");
                cell2 = document.getElementById("process_row"+i+"c2");
                cell3 = document.getElementById("process_row"+i+"c3");
                cell4 = document.getElementById("process_row"+i+"c4");
                cell5 = document.getElementById("process_row"+i+"c5");
            }
            cell0.innerHTML = parsedData[i-1].added;
            cell1.innerHTML = parsedData[i-1].fullpath.replace(/^.*[\\\/]/, '');
            cell2.innerHTML = parsedData[i-1].mediainfo['General'].format;
            cell3.innerHTML = humanFileSize(parsedData[i-1].mediainfo['General'].file_size);
            cell4.innerHTML = parsedData[i-1].status;
            
            var diff;
            if (Date.parse(parsedData[i-1].finished) !== 946681200000) {
                diff = Math.abs(Date.parse(parsedData[i-1].finished) - Date.parse(parsedData[i-1].added));
            } else {
                diff = Math.abs(Date.now() - Date.parse(parsedData[i-1].added));
            }
            var frameProgress = parseFloat(parsedData[i-1].progress)*parseFloat(parsedData[i-1].mediainfo['Video'].frame_count);
            var fps = (parseFloat(frameProgress) / parseFloat(diff/1000)).toFixed(2);
            
            if (parsedData[i-1].status == "Finished") {
                cell5.innerHTML = "100.00% (Ø "+fps+" FPS)";
            } else {
                cell5.innerHTML = (parsedData[i-1].progress*100).toFixed(3)+"% (Ø "+fps+" FPS)";
            }
        }
    }
}

function humanFileSize(bytes, si) {
    var thresh = si ? 1000 : 1024;
    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = si
        ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1)+' '+units[u];
}

function doPoll() {
    $.ajax({
        url: "update",
        start: 0,
        end: 20
    }).done(function (data) {
        append_to_dom(data);
    }).always(function () {
        setTimeout(doPoll, 1000);
    })
}