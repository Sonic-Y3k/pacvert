"use strict";
var document;
var default_start = 0;
var default_end = 20;
var default_status = -1;
var total_files = 0;
var pause_value = 0;
var page_size = 20;

document.addEventListener('keyup', function (){
    if (document.getElementById("editBox").style.visibility != "hidden") {
        if(event.keyCode === 13) { //Enter
            var elem = document.getElementById("saveButton");
            if (typeof elem.onclick == "function") {
                elem.onclick.apply(elem);
            }
        } else if (event.keyCode === 27) { //Esc
            hideEdit();
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
        // Reset page selector
        default_start = 0;
        default_end = page_size;
    
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
    default_end = page_size;
    
    // Remove all entries from table
    $("#table_progress").find("tr:gt(0)").remove();
        
    // Get new data
    pullData(true);
}

function nextPage() {
    if ((default_start+page_size) < total_files) {
        // if possible increase values by page_size
        default_start += page_size;
        default_end += page_size;
        
        // Remove all entries from table
        $("#table_progress").find("tr:gt(0)").remove();
        
        // Get new data
        pullData(true);
    }
}

function previousPage() {
    if ((default_start-page_size) >= 0) {
        // if possible decrease values by page_size
        default_start -= page_size;
        default_end -= page_size;
        
        // Remove all entries from table
        $("#table_progress").find("tr:gt(0)").remove();
        
        // Get new data
        pullData(true);
    }
}

function lastPage() {
    while ((default_start+page_size) < total_files) {
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

function updatePageSize(num) {
    var splitText = document.getElementById("page_selector_text").innerHTML.split(" ");
    splitText[3] = num;
    document.getElementById("page_selector_text").innerHTML = splitText.join(" ");
    page_size = num;
}

function pullData(once = false) {
    $.get("update", {
        start: default_start,
        end: default_end,
        status_filter: default_status
    }).done(function (data) {
        var parsedData = JSON.parse(data);
        if (parsedData === 0) {
            return;
        } else {
            var rowCounter = 0;
            $.each(parsedData, function (index, value) { // iterate over every json value returned
                if (typeof value.queue_length !== 'undefined') {
                    updateTotalFiles(value.queue_length);
                    if (parseInt(value.commits_behind) > 0) {
                    	document.getElementById("update").style.visibility = 'visible';
                    }
                    if (pause_value != parseInt(value.pause)) {
                        toggle_pause(parseInt(value.pause, false));
                    }
                    updatePageSize(value.page_size);
                    return false;
                }
                
                var fullpath = value.file_path+'/'+value.file_name+value.file_extension;
                fullpath = (fullpath.length > 60) ? '...'+fullpath.slice(Math.max(0,fullpath.length-60),fullpath.length) : fullpath;
                var name = ((value.file_rename === null) ? value.file_name+value.file_extension : value.file_rename);
                name += '<a href="#" onclick="javascript:editFileName('+value.unique_id+',\''+fullpath+'\');">';
                name += '<img src="images/white_pencil.svg" class="editpencil" alt="Edit">';
                name += '</a>';

                /*
                This one is quite a little complicated...

                In timedifference we calculate either the difference between the time we started and the time we ended or the time between the time we started and the current time.
                In frameprogress we calculate how many frames we should have archieved by percentage
                In fps we calculate how many frames we are converting in one second
                In progress we just print the values.
                */
                var timedifference = ((Date.parse(value.file_status_finished) !== 946681200000) ? Math.abs(Date.parse(value.file_status_finished) - Date.parse(value.file_status_start)) : Math.abs(Date.now() - Date.parse(value.file_status_start)) );
                var frameProgress = parseFloat(value.file_status_progress)*parseFloat(value.mediainfo.Video.frame_count);
                var fps = (parseFloat(frameProgress) / parseFloat(timedifference/1000)).toFixed(2);
                var eta = (fps > 0) ? msToTime(((parseFloat(value.mediainfo.Video.frame_count) - frameProgress) / fps) * 1000) : "00:00:00.0";
                var elapsed = msToTime(Math.abs(Date.parse(value.file_status_finished) - Date.parse(value.file_status_start)));
                var progress = ((value.file_status_status == 3) ? "100.00%<br>avg. "+fps+" FPS, ET: "+elapsed : (value.file_status_progress*100).toFixed(3)+"%<br>avg. "+fps+" FPS, ETA: "+eta);
                
                var controls = "";
                if ((value.file_status_status !== 0) && (value.file_status_status != 3)) {
                    controls += '<div class="arrows">';
                    controls += '<a href="javascript:moveDown('+value.unique_id+')"><img src="../images/action_arrow_down.svg" class="arrow_down"></a>';
                    controls += '<a href="javascript:moveUp('+value.unique_id+')"><img src="../images/action_arrow_up.svg" class="arrow_up"></a></div>';
                    controls += '<div class="cls_denied"><a href="javascript:remove('+value.unique_id+')"><img src="../images/denied.svg" width="16px" height="16px" class="denied"></a></div>';
                } else if (value.file_status_status == 3) {
                    controls += '<div class="cls_denied"><a href="javascript:remove('+value.unique_id+')"><img src="../images/denied.svg" width="16px" height="16px" class="denied"></a></div>';
                }
                
                var sizetab = humanFileSize(value.file_size);
                if ((value.file_status_status == 0) || (value.file_status_status == 3)) {
                    if (value.file_output_size > 0) {
                        sizetab += " ("+humanFileSize(value.file_output_size)+")";
                    }
                }
                var string_status = 'Undefined';
                switch (value.file_status_status) {
                    case 0:
                        string_status = 'Active';
                        break;
                    case 1:
                        string_status = 'Scanned';
                        break;
                    case 2:
                        string_status = 'Pending';
                        break;
                    case 3:
                        string_status = 'Finished';
                        break;
                    case 4:
                        string_status = 'Failed';
                        break;
                }
                
                var col = [ value.file_status_added,
                            name,
                            value.mediainfo.General.format,
                            sizetab,
                            string_status,
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

function msToTime(duration) {
    var milliseconds = parseInt((duration%1000)/100)
        , seconds = parseInt((duration/1000)%60)
        , minutes = parseInt((duration/(1000*60))%60)
        , hours = parseInt((duration/(1000*60*60))%24);

    hours = (hours < 10) ? "0" + hours : hours;
    minutes = (minutes < 10) ? "0" + minutes : minutes;
    seconds = (seconds < 10) ? "0" + seconds : seconds;

    return hours + ":" + minutes + ":" + seconds + "." + milliseconds;
}

function toggle_pause(value, update=true) {
    var pause = document.getElementById('pause');
    var play = document.getElementById('play');
    
    pause_value = value;
    pause.style.display = pause.style.display === 'none' ? 'inline' : 'none';
    play.style.display = play.style.display === 'none' ? 'inline' : 'none';
    
    if (update === true) {
        $.get( "update", { pause: value });
    }
}

function moveUp(id) {
    $.get( "update", { up: id } );
    $("#table_progress").find("tr:gt(0)").remove();
    pullData(true);
}

function moveDown(id) {
    $.get ( "update", {down: id} );
    $("#table_progress").find("tr:gt(0)").remove();
    pullData(true);
}

function remove(id) {
    $.get ( "update", {remove: id} );
    $("#table_progress").find("tr:gt(0)").remove();
    pullData(true);
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
