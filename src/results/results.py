from flask import Blueprint, render_template, request, redirect, url_for, flash
import configparser
import os
import csv

results_bp = Blueprint(
    'results_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/results/static'
)


@results_bp.route('/results', methods=['GET', 'POST'])
def results_base():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'lookup':
            sessionID = request.form['sessionID']

            return redirect(url_for('results_bp.results', uuid=sessionID))

    return render_template('results.html', music=False)


@results_bp.route('/results/<uuid>', methods=['GET', 'POST'])
def results(uuid):
    cwd = os.getcwd()

    # TODO: The uuid should probably be sanitized

    # Check our generated directory for the submitted session ID
    if os.path.isdir(cwd + '/static/generated/' + uuid):
        musicPath = '/static/generated/' + uuid + '/output.wav'
        dataPath = cwd + '/static/generated/' + uuid + '/data.csv'
        informationPath = cwd + '/static/generated/' + uuid + '/information.ini'

        # Read the information file
        config = configparser.ConfigParser()
        config.read(informationPath)

        query = config['Query']['Query']

        # Read the data file to populate the chart
        labels = []
        values = []
        line = 0
        dataColumn = ''
        amountPoints = 0
        with open(dataPath, mode='r') as dataCSV:
            reader = csv.DictReader(dataCSV)

            for row in reader:
                if line is 0:
                    dataColumn = ','.join(row).split(',')[1]
                    line += 1
                    continue

                labels.append(row['time'])
                values.append(row[dataColumn])
                amountPoints += 1

        legend = 'Queried Data'

        return render_template('results.html', music=True, musicPath=musicPath, sessionID=uuid, labels=labels, values=values, legend=legend, amountPoints=amountPoints, query=query)

    else:
        flash('Session ID \'' + uuid + '\' was not found', 'danger')
        return render_template('results.html', music=False)
