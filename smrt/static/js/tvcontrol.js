var TV = {};

TV.last = "";

TV.checkup = function() {
    $.get("/irc_last", function(data) {
        TV.last = data;
        try {
            if(TV.last.indexOf("refresh") >= 0) document.location.reload(true);
            else if(TV.last.indexOf("view")) {
                area = TV.last.split("view ")[1];
                parts = area.split(" ");
                project = parts[0];
                mile = parts[1];
                date = "";
                if (parts.length >= 3) date = parts[2];
                url = "http://" + window.location.hostname + ":" + window.location.port + "/" + project + "/" + mile + "/" + date;
                window.location.href = url;
            }
        } catch (err) {
            //console.log("oops: " + err);
        }
    });
    setTimeout("TV.checkup();", 2000);
};

$(document).ready(function() {
    setTimeout("TV.checkup();", 2000);
});