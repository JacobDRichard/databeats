from flask import Flask, render_template, request, flash, redirect, url_for, abort
from influxdb import InfluxDBClient
from music21 import *
import subprocess
from datetime import datetime, timedelta
from random import randint
import itertools
import uuid
import os

app = Flask(__name__)
app.secret_key = 'secret'


def influxdb():
    return InfluxDBClient(host='influxdb', port=8086)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/data', methods=['GET', 'POST'])
def data():
    influx = influxdb()
    dict_dbs = influx.get_list_database()
    list_dbs = []

    for db in dict_dbs:
        list_dbs.append(db['name'])

    tuples_dbs = [set(list_dbs[i:i + 4]) for i in range(0, len(list_dbs), 4)]

    datetimeF = datetime.now()
    datetimeF = datetimeF.replace(second=0, microsecond=0)
    datetimeF = str(datetimeF.isoformat('T'))

    if request.method == 'POST':
        button = request.form.get('action')
        action = button.split('-')

        if action[0] == 'create':
            # Grab the entered database name from the form
            dbName = request.form['dbName']

            if len(dbName) != 0 and dbName not in list_dbs:
                # Entered name is verified, create database
                influx.create_database(dbName)

                flash('Database \'' + dbName + '\' was created successfully.', 'success')
                return redirect(url_for('data'))

            else:
                flash('Database \'' + dbName + '\' was not created because it already exists.', 'danger')

        elif action[0] == 'delete':
            # Delete the database on InfluxDB
            influx.drop_database(action[1])

            flash('Database \'' + action[1] + '\' was deleted successfully.', 'success')
            return redirect(url_for('data'))
        elif action[0] == 'generate':
            # Get data submitted from form that is required to be validated
            minimum = int(request.form['min'])
            maximum = int(request.form['max'])
            iterations = int(request.form['iterations'])

            if maximum > minimum > 0 and iterations > 0:
                if iterations < 10000:
                    # Create the JSON with the rest of the form data
                    tagName = request.form['tagName']
                    tagValue = request.form['tagValue']
                    fieldName = request.form['fieldName']

                    datetimeV = request.form['datetime']
                    try:
                        datetimeV = datetime.strptime(datetimeV, '%Y-%m-%dT%H:%M:%S')

                        # Generate randomized time series data
                        queryData = []
                        for x in range(iterations):
                            queryJson = {
                                'measurement': request.form['measurement'],
                                'time': str(datetimeV.isoformat('T')) + 'Z',
                                'fields': {
                                    fieldName: randint(int(request.form['min']), int(request.form['max']))
                                }
                            }

                            if tagName and tagValue is not '':
                                tagJson = {
                                    'tags': {
                                        tagName: tagValue
                                    }
                                }

                                queryJson.update(tagJson)

                            queryData.append(queryJson)

                            interval = request.form['interval']
                            if interval == 'Minute':
                                datetimeV += timedelta(minutes=1)
                            elif interval == 'Hourly':
                                datetimeV += timedelta(hours=1)

                        # Swap to selected database
                        database = request.form['database']
                        influx.switch_database(database)

                        # Submit generated data to InfluxDB
                        result = influx.write_points(queryData)

                        if result:
                            flash('Submitted generated time series data to database \'' + database + '\' successfully.',
                                  'success')
                        else:
                            flash('Failed to submit generated time series data to database \'' + database + '\'.',
                                  'danger')

                    except ValueError:
                        flash('Failed to parse submitted datetime.', 'danger')
                else:
                    flash('Iterations must be less than 10000.', 'danger')

            else:
                flash('The maximum field must be greater than the minimum field which must be greater than 0. '
                      'Iterations must be greater than 0.',
                      'danger')

    return render_template('data.html', datetimeF=datetimeF, tuples_dbs=tuples_dbs, list_dbs=list_dbs)


@app.route('/sonify', methods=['GET', 'POST'])
def sonify():
    influx = influxdb()
    dict_dbs = influx.get_list_database()
    list_dbs = []

    for db in dict_dbs:
        list_dbs.append(db['name'])

    datetimeS = datetime.now()
    datetimeS = datetimeS.replace(second=0, microsecond=0)
    datetimeE = datetimeS
    datetimeS = str(datetimeS.isoformat('T'))
    datetimeE += timedelta(days=1)
    datetimeE = str(datetimeE.isoformat('T'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'query':
            database = request.form['database']
            measurement = request.form['measurement']
            field = request.form['field']

            tagName = ''
            if 'tagName' in request.form:
                tagName = request.form['tagName']

            tagValue = ''
            if 'tagValue' in request.form:
                tagValue = request.form['tagValue']

            datetimeStart = request.form['datetimeStart']
            datetimeEnd = request.form['datetimeEnd']

            # Check the submitted datetime data
            start = ''
            try:
                start = datetime.strptime(datetimeStart, '%Y-%m-%dT%H:%M:%S')

            except ValueError:
                # Failed to parse, compatibility check across browsers, some do not include seconds
                try:
                    start = datetime.strptime(datetimeStart + ':00', '%Y-%m-%dT%H:%M:%S')

                except ValueError:
                    # Unable to parse the submitted data, flash error
                    flash('Unable to parse the submitted start datetime.', 'danger')

            start = datetime.strftime(start, '%Y-%m-%dT%H:%M:%S') + 'Z'

            end = ''
            try:
                end = datetime.strptime(datetimeEnd, '%Y-%m-%dT%H:%M:%S')

            except ValueError:
                # Failed to parse, compatibility check across browsers, some do not include seconds
                try:
                    end = datetime.strptime(datetimeEnd + ':00', '%Y-%m-%dT%H:%M:%S')

                except ValueError:
                    # Unable to parse the submitted data, flash error
                    flash('Unable to parse the submitted start datetime.', 'danger')

            end = datetime.strftime(end, '%Y-%m-%dT%H:%M:%S') + 'Z'

            tagSection = ''
            if tagName and tagValue is not '':
                tagSection = ' AND \"' + tagName + '\"=\'' + tagValue + '\''

            # Create query from submitted form data
            query = 'SELECT ' + field + ' AS data FROM \"' + database + '\".\"autogen\".\"' + measurement \
                    + '\" WHERE time > \'' + start + '\' AND time < \'' + end + '\'' + tagSection

            print(query)

            result = influx.query(query).raw

            resultDataList = result['series']

            if len(resultDataList):
                # Query returned data, generate random session ID
                sessionID = str(uuid.uuid4())

                # Grab minimum and maximum value for scaling
                resultData = resultDataList[0]['values']
                resultsDict = {point[0]: point[1] for point in resultData}

                minValue = resultsDict[min(resultsDict, key=resultsDict.get)]
                maxValue = resultsDict[max(resultsDict, key=resultsDict.get)]

                # Create a new list and scale the results to 1-8
                noteValues = []
                for point in resultData:
                    noteValues.append(round((((8 - 1) * (point[1] - minValue)) / (maxValue - minValue)) + 1))

                noteStream = stream.Stream()
                for noteV in noteValues:
                    if noteV == 1:
                        noteStream.append(note.Note('C3'))
                    elif noteV == 2:
                        noteStream.append(note.Note('D3'))
                    elif noteV == 3:
                        noteStream.append(note.Note('E3'))
                    elif noteV == 4:
                        noteStream.append(note.Note('F3'))
                    elif noteV == 5:
                        noteStream.append(note.Note('G3'))
                    elif noteV == 6:
                        noteStream.append(note.Note('A3'))
                    elif noteV == 7:
                        noteStream.append(note.Note('B3'))
                    elif noteV == 8:
                        noteStream.append(note.Note('C4'))

                noteStream.write('midi', 'midi_' + sessionID + '.midi')

                # Create session directory
                cwd = os.getcwd()
                if not os.path.isdir(cwd + '/static/generated'):
                    # Create our generated directory if it doesn't already exist
                    os.mkdir(cwd + '/static/generated')

                os.mkdir(cwd + '/static/generated/' + sessionID)

                # Convert midi to wav
                # fluidsynth -ni -F output.wav -r 44100 SF.sf2 test.midi
                outName = cwd + '/static/generated/' + sessionID + '/output.wav'
                midiName = 'midi_' + sessionID + '.midi'
                subprocess.call(['fluidsynth', '-ni', '-F', outName, '-r', '44100', 'SF.sf2', midiName])

                # Get path of the generated music
                musicPath = '/static/generated/' + sessionID + '/output.wav'

                # Cleanup old files
                os.remove(cwd + '/midi_' + sessionID + '.midi')

                # Make the chart
                legend = 'Queried Data'

                labels = []
                values = []
                for point in resultData:
                    labels.append(point[0])
                    values.append(point[1])

                return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs,
                                       legend=legend, labels=labels, values=values, music=True, musicPath=musicPath,
                                       sessionID=sessionID)

            else:
                flash('Query did not return any data, please try again.', 'danger')
        elif action == 'lookup':
            cwd = os.getcwd()
            sessionID = request.form['sessionID']

            # TODO: The sessionID should probably be sanitized

            # Check our generated directory for the submitted session ID
            if os.path.isdir(cwd + '/static/generated/' + sessionID):
                musicPath = '/static/generated/' + sessionID + '/output.wav'

                return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs,
                                       music=True, musicPath=musicPath, sessionID=sessionID)

            else:
                flash('A session with an ID of \'' + sessionID + '\' was not found.', 'danger')

    return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs, music=False)


@app.route('/database/get_measurements')
def get_measurements():
    influx = influxdb()
    database = request.args.get('database')

    dict_dbs = influx.get_list_database()
    list_dbs = []

    for db in dict_dbs:
        list_dbs.append(db['name'])

    if database in list_dbs:
        influx.switch_database(database)
        measurements = influx.get_list_measurements()

        response = {}
        for measurement in measurements:
            measurementJson = {
                measurement['name']: measurement['name']
            }

            response.update(measurementJson)

        if response:
            return response
        else:
            return {}
    else:
        abort(404)


@app.route('/database/get_series/get_tag_names')
def get_tag_names():
    influx = influxdb()
    database = request.args.get('database')
    measurement = request.args.get('measurement')

    influx.switch_database(database)

    list_series = influx.get_list_series(measurement=measurement)

    response = {}
    for series in list_series:
        series = series.split(',')

        if series[0] == measurement and len(series) > 1:
            tags = series[1]
            tags = tags.split('=')

            if tags[0] and tags[1] is not '':
                tagName = {
                    tags[0]: tags[0]
                }

                response.update(tagName)

    if response:
        return response
    else:
        return {}


@app.route('/database/get_series/get_tag_values')
def get_tag_values():
    influx = influxdb()
    database = request.args.get('database')
    measurement = request.args.get('measurement')
    tagName = request.args.get('tagName')

    influx.switch_database(database)

    list_series = influx.get_list_series(measurement=measurement)

    response = {}
    for series in list_series:
        series = series.split(',')

        if series[0] == measurement and len(series) > 1:
            tags = series[1]
            tags = tags.split('=')

            if tags[0] and tags[1] is not '':
                if tags[0] == tagName:
                    tagValue = {
                        tags[1]: tags[1]
                    }

                    response.update(tagValue)

    if response:
        return response
    else:
        return {}


@app.route('/database/get_series/get_fields')
def get_fields():
    influx = influxdb()
    database = request.args.get('database')
    measurement = request.args.get('measurement')

    influx.switch_database(database)

    # TODO: Potential attack vector, sanitize input here
    query = 'SHOW FIELD KEYS FROM ' + measurement

    fields = list(itertools.chain.from_iterable([x.values() for x in (influx.query(query).get_points())]))
    fields = fields[::2]

    response = {}
    for field in fields:
        fieldJson = {
            field: field
        }

        response.update(fieldJson)

    if response:
        return response
    else:
        return {}


@app.context_processor
def utility_functions():
    def print_in_console(message):
        print(message)

    return dict(mdebug=print_in_console)


if __name__ == '__main__':
    app.jinja_env.add_extension('jinja2.ext.do')
    app.run(host='localhost')
