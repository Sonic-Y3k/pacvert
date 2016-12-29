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
                row.className = "listelement";
                
                for (var j = 0; j <= 5; j++) {
                    eval('cell'+j+' = row.insertCell('+j+')');
                    eval('cell'+j+'.classname = "col'+j+'"')
                    eval('cell'+j+'.id = "process_row'+i+'c'+j+'"');
                }
            } else {
                for (var g = 0; g <= 5; g++) {
                    eval('cell'+g+' = document.getElementById("process_row'+i+'c'+g+'")');
                }
            }
            cell0.innerHTML = parsedData[i-1].added;
            cell1.innerHTML = '<span class="open" id="open">'+parsedData[i-1].fullpath.replace(/^.*[\\\/]/, '')+'</span>';
            cell1.innerHTML += '<span id="open" class="open"><a href="#" onclick="javascript:editFileName('+i+',\''+parsedData[i-1].fullpath+'\');"><img src="images/white_pencil.svg" width="10" align="right" style="cursor: pointer;" id="r'+i+'e" alt="Edit"/></a></span>';
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

function restoreBlur(id) {
    var newName = document.getElementById("editBoxNewFilename").value;
    $.get( "update", { start: 0, end: 20, updateName: newName, updateID: id } ).done(function( data ) {
        if (data == "OK.") {
            removeBlur();
        } else {
            document.getElementById("returnValue").innerHTML = data;
        }
    });    
}

function removeBlur() {
    document.getElementById("editBox").style.visibility = 'hidden';
    //document.getElementById("oval").style = "border-radius: 15px;border: none;padding: 10px;width: calc(100% - 20px);height: auto ?;background-color: rgb(40,40,40);";
    document.getElementById("oval").style.filter = "none";
    document.getElementById("oval").style.opacity = 1.0;
    document.getElementById("returnValue").innerHTML = "";
}

function editFileName(id, filename) {
    document.getElementById("oval").style.filter = "blur(2px)";
    document.getElementById("oval").style.opacity = 0.4;
    //document.getElementById("oval").style = "border-radius: 15px;border: none;padding: 10px;width: calc(100% - 20px);height: auto ?;background-color: rgb(40,40,40);-webkit-filter: blur(2px);-moz-filter: blur(2px);-o-filter: blur(2px);-ms-filter: blur(2px);";
    document.getElementById("editBoxOriginalFilename").innerHTML = filename;
    document.getElementById("editBox").style.visibility = 'visible';

    document.getElementById("editBoxNewFilename").value = filename.replace(/^.*[\\\/]/, '');
    document.getElementById("editBoxNewFilename").onclick = function() { document.getElementById("editBoxNewFilename").setSelectionRange(0, document.getElementById("editBoxNewFilename").value.length); };
    document.getElementById("saveButton").onclick = function() { restoreBlur(id-1); };
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