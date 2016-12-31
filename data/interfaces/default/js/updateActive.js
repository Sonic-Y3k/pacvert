"use strict";
var document;
function append_to_dom(data) {
    var parsedData = JSON.parse(data);
    if (parsedData.length === 0) {
        return;
    }
    
    var table = document.getElementById("to_process");
    if (table !== null) { //table element does exist
        if (parsedData.length < table.rows.length) {
            //for (var h = parsedData.length+1; h < table.rows.length; h++) {
            //    table.deleteRow(h);
            //}
            $("#to_process").find("tr:gt(0)").remove();
        }
        
        for (var i = 1; i <= parsedData.length; i++) {
            var row = document.getElementById("process_row"+i);
            setTotalValue(parsedData[i-1].queuelength);
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
                diff = Math.abs(Date.parse(parsedData[i-1].finished) - Date.parse(parsedData[i-1].timestarted));
            } else {
                diff = Math.abs(Date.now() - Date.parse(parsedData[i-1].timestarted));
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

function getStartValue() {
    return Number(document.getElementById("startval").value);
}

function getEndValue() {
    return Number(document.getElementById("endval").value);
}

function getTotalValue() {
    var splitText = document.getElementById("page_selector_text").innerHTML.split(" ");
    return Number(splitText[5]);
}

function setTotalValue(newValue) {
    var splitText = document.getElementById("page_selector_text").innerHTML.split(" ");
    splitText[5] = newValue;
    document.getElementById("page_selector_text").innerHTML = splitText.join(" ");
}

function nextPage() {
    var start = getStartValue()+20;
    var totalMinimum = Math.min(Math.max(0, start), getTotalValue()-(getTotalValue() % 20));
    
    var totalMaximum;
    if (totalMinimum === 0) {
        totalMaximum = Math.min(19, getTotalValue());
    } else {
        totalMaximum = totalMinimum + 19;
    }
    
    document.getElementById("startval").value = totalMinimum;
    document.getElementById("endval").value = totalMaximum;  
}

function previousPage() {
    var start = getStartValue()-20;
    var totalMinimum = Math.max(0, start);
    var totalMaximum;
    if (totalMinimum === 0) {
        totalMaximum = Math.min(19, getTotalValue());
    } else {
        totalMaximum = totalMinimum + 19;
    }
    
    document.getElementById("startval").value = totalMinimum;
    document.getElementById("endval").value = totalMaximum;
}

function updatePagePosition() {
    var splitText = document.getElementById("page_selector_text").innerHTML.split(" ");
    splitText[1] = getStartValue()+1;
    splitText[3] = Math.min(getEndValue()+1, getTotalValue());
    document.getElementById("page_selector_text").innerHTML = splitText.join(" ");
}

function removeBlur() {
    document.getElementById("editBox").style.visibility = 'hidden';
    document.getElementById("oval").style.filter = "none";
    document.getElementById("oval").style.opacity = 1.0;
    document.getElementById("returnValue").innerHTML = "";
}

function editFileName(id, filename) {
    document.getElementById("oval").style.filter = "blur(2px)";
    document.getElementById("oval").style.opacity = 0.4;
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

function deleteRows() {
    var table = document.getElementById("to_process");
    var mod = (getEndValue() - getStartValue());
    if (mod < table.rows.length && mod > 0)  {
        for (var h=mod; h<table.rows.length; h++) {
            table.deleteRow(h);
        }

    }
      
}

function doPoll() {
    $.get("update", {
        start: getStartValue(),
        end: getEndValue()
    }).done(function (data) {
        append_to_dom(data);
        updatePagePosition();
        deleteRows();
    }).always(function () {
        setTimeout(doPoll, 1000);
    })
}