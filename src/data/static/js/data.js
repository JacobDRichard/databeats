$(function () {
    let select = {
        datetime: $('#datetime'),
        interval: $('#interval'),
        iterations: $('#iterations'),
    }

    function updateEndDatetime() {
        let datetime = new Date(select.datetime.val());
        let interval = select.interval.val();
        let iterations = parseInt(select.iterations.val(), 10);
        const offset = datetime.getTimezoneOffset()
        datetime = new Date(datetime.getTime() - (offset * 60 * 1000))

        let temp = new Date(datetime);
        if(interval === 'Second') {
            datetime.setSeconds(temp.getSeconds() + iterations);
        } else if(interval === 'Minute') {
            datetime.setMinutes(temp.getMinutes() + iterations);
        } else if(interval === 'Hourly') {
            datetime.setHours(temp.getHours() + iterations);
        }

        document.getElementById('endDatetime').innerHTML = datetime.toISOString().split('.')[0] + 'Z';
    }

    select.datetime.on('change', function () {
        updateEndDatetime();
    });

    select.interval.on('change', function () {
        updateEndDatetime();
    });

    select.iterations.on('change', function () {
        updateEndDatetime();
    });

    updateEndDatetime();
});