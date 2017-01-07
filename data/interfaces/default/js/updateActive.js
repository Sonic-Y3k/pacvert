"use strict";
var document;
var default_start = 0;
var default_end = 20;
var default_status = -1;
var total_files = 0;

document.addEventListener('keyup', function (){
    if (document.getElementById("editBox").style.visibility != "hidden") {
        if(event.keyCode === 13) { //Enter
            var elem = document.getElementById("saveButton");
            if (typeof elem.onclick == "function") {
                elem.onclick.apply(elem);
            }
        } else if (event.keyCode === 27) { //Esc
            removeBlur();
        }
    }
});

function showFilter(evt, settingCat, num) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the link that opened the tab
    document.getElementById(settingCat).style.display = "block";
    evt.currentTarget.className += " active";

    if (settingCat == "progress") { // only do this if displaying progress window
        // Set the filter so that the right data is pulled
        default_status = num;
    
        // Remove all entries from table
        $("#table_progress").find("tr:gt(0)").remove();
        
        // Get new data
        pullData(true);
    }
}

function firstPage() {
    // Restore default value
    default_start = 0;
    default_end = 20;
    
    // Remove all entries from table
    $("#table_progress").find("tr:gt(0)").remove();
        
    // Get new data
    pullData(true);
}

function nextPage() {
    if ((default_start+20) < total_files) {
        // if possible increase values by 20
        default_start += 20;
        default_end += 20;
        
        // Remove all entries from table
        $("#table_progress").find("tr:gt(0)").remove();
        
        // Get new data
        pullData(true);
    }
}

function previousPage() {
    if ((default_start-20) >= 0) {
        // if possible decrease values by 20
        default_start -= 20;
        default_end -= 20;
        
        // Remove all entries from table
        $("#table_progress").find("tr:gt(0)").remove();
        
        // Get new data
        pullData(true);
    }
}

function lastPage() {
    while ((default_start+20) < total_files) {
        // increase by 20 unitl we are on the last possible page
        nextPage();
    }
}

function updateTotalFiles(count) {
    var splitText = document.getElementById("page_selector_text").innerHTML.split(" ");
    splitText[5] = count;
    document.getElementById("page_selector_text").innerHTML = splitText.join(" ");
    total_files = count;
}

function pullData(once = false) {
    $.get("update", {
        start: default_start,
        end: default_end,
        statusFilter: default_status
    }).done(function (data) {
        var parsedData = JSON.parse(data);
        if (parsedData === 0) {
            return;
        } else {
            var rowCounter = 0;
            
            $.each(parsedData, function (index, value) { // iterate over every json value returned
                updateTotalFiles(value.queuelength);
                
                var name = ((value.rename === null) ? value.fullpath.replace(/^.*[\\\/]/, '') : value.rename);
                name += '<a href="#" onclick="javascript:editFileName('+value.id+',\''+value.fullpath+'\');">';
                name += '<img src="images/white_pencil.svg" class="editpencil" alt="Edit">';
                name += '</a>';
                
                /*
                This one is quite a little complicated...
                
                In timedifference we calculate either the difference between the time we started and the time we ended or the time between the time we started and the current time.
                In frameprogress we calculate how many frames we should have archieved by percentage
                In fps we calculate how many frames we are converting in one second
                In progress we just print the values.
                */
                var timedifference = ((Date.parse(value.finished) !== 946681200000) ? Math.abs(Date.parse(value.finished) - Date.parse(value.timestarted)) : Math.abs(Date.now() - Date.parse(value.timestarted)) );
                var frameProgress = parseFloat(value.progress)*parseFloat(value.mediainfo.Video.frame_count);
                var fps = (parseFloat(frameProgress) / parseFloat(timedifference/1000)).toFixed(2);
                var progress = ((value.status == "Finished") ? "100.00% (avg. "+fps+" FPS)" : (value.progress*100).toFixed(3)+" (avg. "+fps+" FPS)");
                
                var controls = "";
                if ((value.status != "Active") && (value.status != "Finished")) {
                    controls += '<div class="arrows"><a href="javascript:moveDown('+value.id+')"><img src="../images/action_arrow_down.svg" class="arrow_down"></a>';
                    controls += '<a href="javascript:moveUp('+value.id+')"><img src="../images/action_arrow_up.svg" class="arrow_up"></a>';
                    controls += '<a href="javascript:remove('+value.id+')"><img src="../images/denied.svg" width="16px" height="16px" class="denied"></a></div>';
                } else if (value.status == "Finished") {
                    controls += '<div class="arrows"><a href="javascript:remove('+value.id+')"><img src="../images/denied.svg" width="16px" height="16px" class="denied"></a></div>';
                }
                
                var col = [ value.added,
                            name,
                            value.mediainfo.General.format,
                            humanFileSize(value.mediainfo.General.file_size),
                            value.status,
                            progress,
                            controls];
                
                if (rowCounter > ($('#table_progress tr').length-2)) {
                    var styleclass = (rowCounter % 2 === 0) ? "listelement_even" : "listelement_odd";
                    var row = "<tr id='tr_"+rowCounter+"' class='"+styleclass+"'><td class='col_timeadded'>"+col.join("</td><td>")+"</td></tr>"; 
                    $('#table_progress').append(row);
                } else {
                    var cols = $('#tr_'+rowCounter).find("td");
                    
                    for (var i=0; i < col.length; i++) {
                        if (cols.eq(i).html() != col[i]) {
                            cols.eq(i).html(col[i]);
                        }
                    }
                }
                
                rowCounter += 1;
            });
        }
    }).always(function () {
        if ( once === false ) {
            setTimeout(pullData, 1000);
        }
    });
}

function moveUp(id) {
    $.get( "update", { up: id } );
}

function moveDown(id) {
    $.get ( "update", {down: id} );
}

function remove(id) {
    $.get ( "update", {remove: id} );
}

function displayEdit() {
    document.getElementById("oval").style.filter = "blur(2px)";
    document.getElementById("oval").style.opacity = 0.4;
    document.getElementById("editBox").style.visibility = 'visible';
}

function hideEdit() {
    document.getElementById("editBox").style.visibility = 'hidden';
    document.getElementById("oval").style.filter = "none";
    document.getElementById("oval").style.opacity = 1.0;
    document.getElementById("returnValue").innerHTML = "";
}

function editFileName(id, filename) {
    displayEdit();
    
    document.getElementById("editBoxOriginalFilename").innerHTML = filename;
    document.getElementById("editBoxNewFilename").value = filename.replace(/^.*[\\\/]/, '');
    document.getElementById("editBoxNewFilename").onclick = function() { document.getElementById("editBoxNewFilename").setSelectionRange(0, document.getElementById("editBoxNewFilename").value.length); };
    document.getElementById("saveButton").onclick = function() { pushNewName(id); };
}

function pushNewName(id) {
    var newName = document.getElementById("editBoxNewFilename").value.replace(/^.*[\\\/]/, '');
    $.get( "update", { updateName: newName, updateID: id } ).done(function( data ) {
        if (data == "OK.") {
            hideEdit();
        } else {
            document.getElementById("returnValue").innerHTML = data;
        }
    });
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