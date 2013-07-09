function translateArraysToSeries(lines) {
    var tixtotals = [];
    var tixunpointed = [];
    var dev = [];
    var qa = [];
    var totals = [];
    var xaxis = [];
    var pmax = 0;
    var tmax = 0;
    for (x in lines) {
        data = lines[x];
        if (data[0] == "") {continue;}
        tixtotals.push([data[0],data[1]]);
        tixunpointed.push([data[0],data[2]]);
        dev.push([data[0],data[3]]);
        qa.push([data[0],data[4]]);
        totals.push([data[0], data[5]]);
        console.log("pre:: "+data[3]);
        console.log("post:: "+parseInt(data[3]));
        pmax = Math.max(pmax, parseInt(data[3]), parseInt(data[4]), parseInt(data[5]));
        tmax = Math.max(tmax, parseInt(data[1]), parseInt(data[2]));
    }
    return {
        points: {
            y_high: pmax, data: [totals, dev, qa]
        },
        tickets: {
            y_high: tmax, data: [tixtotals, tixunpointed]
        }
    };
}

function plotChart(data) {
    var points_data = data["points"]["data"];
    var tickets_data = data["tickets"]["data"];
    var points = $.jqplot('points', points_data,
        {
          title:'Milestone points over time',
          // Series options are specified as an array of objects, one object
          // for each series.
          axes: {
              yaxis: {
                  min: 0,
                  max: data["points"]["y_high"]
              },
              xaxis: {
                  renderer:$.jqplot.DateAxisRenderer
              }
          },
          seriesDefaults: {
              show: true
          },
          series:[
              {
                label: "Total"
              },
              {
                label: "Dev"
              },
              {
                label: "QA"
              }
          ],
          legend: {
              show: true
          },
        }
    );
    var tickets = $.jqplot('tickets', tickets_data,
        {
          title:'Milestone tickets over time',
          // Series options are specified as an array of objects, one object
          // for each series.
          axes: {
              yaxis: {
                  min: 0,
                  max: data["tickets"]["y_high"]
              },
              xaxis: {
                  renderer:$.jqplot.DateAxisRenderer
              }
          },
          seriesDefaults: {
              show: true
          },
          series:[
              {
                label: "Total"
              },
              {
                label: "Upointed"
              }
          ],
          legend: {
              show: true
          },
        }
    );
}