var resultsChart;

function createChart(labels, values, legend) {
    Chart.defaults.global.responsive = false;

    // Initialize chart with the data
    var chartData = {
        labels: labels,
        datasets: [{
            label: legend,
            fill: false,
            lineTension: 0.1,
            borderColor: "rgba(75,192,192,1)",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(75,192,192,1)",
            pointBackgroundColor: "rgba(75,192,192,1)",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(75,192,192,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 5,
            pointHitRadius: 10,
            data: values,
            spanGaps: false,
        }]
    }

    // get chart canvas
    var ctx = document.getElementById("resultsChart").getContext("2d");

    // create the chart using the chart canvas
    resultsChart = new Chart.Line(ctx, {
        type: 'line',
        data: chartData
    });
}

var reqId;
var music = document.getElementById("music");
var amountPoints = 0;

var startTracking = function () {
    var timePerPoint = music.duration * 1000 / amountPoints;
    reqId = requestAnimationFrame(function play() {
        var currentTime = Math.round(music.currentTime * 1000);

        resultsChart.data.datasets[0].pointBackgroundColor = function (context) {
            var index = context.dataIndex;

            if (currentTime >= index * timePerPoint && currentTime < (index + 1) * timePerPoint) {
                return 'red';
            }

            return 'rgba(75,192,192,1)'
        };
        resultsChart.update();

        reqId = requestAnimationFrame(play);
    });
};

var stopTracking = function () {
    if (reqId) {
        cancelAnimationFrame(reqId);
    }
};

function startListeners(points) {
    amountPoints = points
    music = document.getElementById("music");
    music.addEventListener('play', startTracking);
    music.addEventListener('pause', stopTracking);
}
