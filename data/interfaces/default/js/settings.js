function openSettings(evt, settingCat) {
    // Declare all variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("settingcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("settinglinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the link that opened the tab
    document.getElementById(settingCat).style.display = "block";
    evt.currentTarget.className += " active";
}

function fillSettings(name, content) {
    // As content is a dict itself we need to get the value and type from it
    var value = content.value;
    var type = content.type;
    
    // Not every single setting is working as of now. And the user doesn't need to see everything.
    var ignore = [  'LOG_BLACKLIST',
                    'HTTP_USERNAME',
                    'HTTPS_CREATE_CERT',
                    'ENABLE_HTTPS',
                    'HTTP_ENVIRONMENT',
                    'HTTPS_KEY',
                    'CHECK_GITHUB_ON_STARTUP',
                    'GIT_TOKEN',
                    'HTTPS_CERT',
                    'HTTP_BASIC_AUTH',
                    'GIT_USER',
                    'HTTP_HASH_PASSWORD',
                    'DO_NOT_OVERRIDE_GIT_BRANCH',
                    'HTTP_PASSWORD',
                    'HTTP_HOST',
                    'GIT_BRANCH',
                    'HTTP_ROOT',
                    'HTTPS_IP',
                    'HTTP_PROXY',
                    'GIT_PATH',
                    'FIRST_RUN_COMPLETE',
                    'HTTP_HASHED_PASSWORD',
                    'HTTPS_DOMAIN',
                    'INTERFACE'];
    
    if (ignore.indexOf(name) === -1) { // If current item is not in the ignore list
        if (name.indexOf("CODEC_") === -1) { // check if item name starts with "CODEC". Than this is a General configuration variable
            fillSettingDiv(name, type, value, "General"); // add a setting to general div
        } else if (name.indexOf("DEFAULT_CODEC") !== -1) { 
            fillSettingDiv(name, type, value, "Codec"); // add a setting to default codec div
        } else if ((name.indexOf("CODEC_") !== -1) && (name.indexOf("H264") !== -1)) {
            fillSettingDiv(name, type, value, "x264"); // add a setting to x264 div
        } else if ((name.indexOf("CODEC_") !== -1) && (name.indexOf("HEVC") !== -1)) {
            fillSettingDiv(name, type, value, "x265"); // add a setting to x265 div
        }
    }
}

function fillSettingDiv(name, type, value, category) {
    if (name == "DEFAULT_CODEC_VIDEO") { // Altough DEFAULT_CODEC_VIDEO is a string variable, it's easier to build a dropdown box for this.
        $("#table_"+category.toLowerCase()).append("<tr><td>"+name+":</td><td><select name='"+name+"' id='"+name+"' class='setting'><option value='hevc'>HEVC (x265)</option><option value='x264'>x264</option></select><td></tr>");
        document.getElementById(name).selectedIndex = ((value === "hevc") ? 0 : 1); // set selected value to either x264 or hevc
    } else {
        if (type == "bool") { // Boolean is represented by a dropdown box with the string representation of enabled and disabled.
            var selectID = ((Number(value) === 0) ? 0 : 1);
            $("#table_"+category.toLowerCase()).append("<tr><td>"+name+":</td><td><select name='"+name+"' id='"+name+"' class='setting'><option value='false'>Disabled</option><option value='true'>Enabled</option></select><td></tr>");
            document.getElementById(name).selectedIndex = selectID;
        } else if ((type == "str") || (type == "int") || (type == "float")) { // Strings, floats and ints are displayed via an edit field
            $("#table_"+category.toLowerCase()).append("<tr><td>"+name+":</td><td><input class='setting' name='"+name+"' value='"+value+"'></td></tr>");
        } else if (type == "dict") { // Dict need to be splitted into something everyone can read
            
            var joinedData = "";
            for (var key in value) {
                if (joinedData.length < 1) {
                   joinedData = key+":"+value[key]; // the variable name is followed by a : and its value
                } else {
                    joinedData += ","+key+":"+value[key]; // if this is not the first element, just add a leading comma.
                }
            }
            $("#table_"+category.toLowerCase()).append("<tr><td>"+name+":</td><td><input class='setting' name='"+name+"' value='"+joinedData+"'></td></tr>");
        } else {
            $("#table_"+category.toLowerCase()).append("<tr><td>"+name+":</td><td>"+value+" ("+type+")</td></tr>");
        }
    }
}

function getConfigurableValues() {
    $.get("settings", {
        getConfigVal: 1
    }).done(function(data) {
        var parsedData = JSON.parse(data);
        $.each(parsedData.General, function (name, content) {
            fillSettings(name, content);
        });
        $.each(parsedData.CodecSettings, function (name, content) {
            fillSettings(name, content);
        });
    });
}

function saveConfigurableValues() {
    $(".setting").each(function( i, obj ) {
        var name = obj.name;
        var value = obj.value;
        $.get("settings", {
            paramName: name,
            paramVal: value
        }).done(function (data) {
            if (data != "OK.") {
                alert("Error. Cannot update "+name+" to "+value);
                return false;
            }
        });
    });
    alert("Settings were successfully saved.");
}

$(document).ready(getConfigurableValues());