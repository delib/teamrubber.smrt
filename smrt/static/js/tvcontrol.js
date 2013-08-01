var TV = {};

TV.last = "";

TV.panels = {
    "row_count": 1,
    "rows": [
        {
            "col_count": 1,
            "cols": [
                "http://127.0.0.1:8080/",
            ]
        }
    ]
}

TV.checkup = function() {
    $.get("/irc_last", function(data) {
        try {
            TV.last = data.replace(": ", "");
            console.log(TV.last);
            if(TV.last.indexOf("refresh") >= 0) document.location.reload(true);
            else if(TV.last.indexOf("view") >= 0) {
                area = TV.last.split("view ")[1];
                parts = area.split(" ");
                project = parts[0];
                mile = parts[1];
                date = "";
                if (parts.length >= 3) date = parts[2];
                url = "http://" + window.location.hostname + ":" + window.location.port + "/" + project + "/" + mile + "/" + date;
                window.location.href = url;
            } else if(TV.last.indexOf("panels") >= 0) {
                parts = TV.last.split(" ");
                console.log(parts);
                if (parts[1] == "add" && parts[2] == "row") {
                    // Format is "panels add row"
                    TV.panels["row_count"] += 1;
                    TV.panels["rows"].push({});
                    TV.draw_grid();
                } else if(parts[1] == "add" && parts[2] == "col") {
                    // Format is "panels add col to [ROW_INDEX] [WEB_ADDRESS]"
                    row_index = parseInt(parts[4]);
                    if(row_index < TV.panels["row_count"]) {
                        row = TV.panels["rows"][row_index];
                        row["col_count"] += 1;
                        row["cols"].push(parts[5]);
                    }
                } else if(parts[1] == "set") {
                    // Format is "panels set row [ROW_INDEX] col [COL_INDEX] [WEB_ADDRESS]"
                    TV.panels["rows"][parseInt(parts[3])]["cols"][parseInt(parts[5])] = parts[6];
                    TV.draw_grid();
                } else if(parts[1] == "clear") {
                    TV.panels["row_count"] = 1;
                    TV.panels["rows"].length = 0;
                    TV.panels.push({ "col_count": 1, "cols": [ "http://127.0.0.1:8080/", ] });
                    TV.draw_grid();
                }
                TV.draw_grid();
            }
        } catch (err) {
            //console.log("oops: " + err);
        }
    });
    setTimeout("TV.checkup();", 2000);
};

TV.fail = false;

TV.draw_grid = function() {
    $("div").each(function() { $(this).remove(); });
    // Start drawing out a grid
    var classes = ["one", "two", "three", "four"]
    var row_class = classes[(TV.panels["row_count"] - 1)];
    // Create elements and append
    for (var i = 0; i < TV.panels["row_count"]; i++) {
        var row_obj = TV.panels["rows"][i];
        var row = document.createElement("div");
        row.className = "tv_row " + row_class;
        row.id = "row-" + (i + 1);
        document.getElementsByTagName("body")[0].appendChild(row);
        for(var j = 0; j < row_obj["col_count"]; j++) {
            var col = document.createElement("iframe");
            col.className = "tv_column " + classes[(row_obj["col_count"] - 1)];
            col.src = row_obj["cols"][j];
            col.id = "row-" + (i+1) + "-col-" + (j+1);
            row.appendChild(col);
        }
    }
};

$(document).ready(function() {
    setTimeout("TV.checkup();", 2000);
});