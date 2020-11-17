from flask import Blueprint, render_template, request, flash
from settings import settings
import os
import subprocess
import uuid
from datetime import datetime, timedelta
import csv
from music21 import *

sonify_bp = Blueprint(
    'sonify_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/sonify/static'
)


@sonify_bp.route('/sonify', methods=['GET', 'POST'])
def sonify():
    influx = settings.influxdb()
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

                # Save queried data into file for when the user looks up the session ID
                with open(cwd + '/static/generated/' + sessionID + '/data.csv', mode='w') as dataCSV:
                    columns = ['time', measurement + '.' + field]
                    writer = csv.DictWriter(dataCSV, fieldnames=columns)

                    writer.writeheader()
                    for point in resultData:
                        writer.writerow({'time': point[0], measurement + '.' + field: point[1]})

                # Save query for when the user looks up the session ID
                queryFile = open(cwd + '/static/generated/' + sessionID + '/query.txt', 'w')
                queryFile.write(query)
                queryFile.close()

                # Cleanup old files
                os.remove(cwd + '/midi_' + sessionID + '.midi')

                # Make the chart
                legend = 'Queried Data'

                labels = []
                values = []
                amountPoints = 0
                for point in resultData:
                    labels.append(point[0])
                    values.append(point[1])
                    amountPoints += 1

                influx.close()
                return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs,
                                       legend=legend, labels=labels, values=values, music=True, musicPath=musicPath,
                                       sessionID=sessionID, amountPoints=amountPoints, query=query)

            else:
                flash('Query did not return any data, please try again.', 'danger')
        elif action == 'lookup':
            cwd = os.getcwd()
            sessionID = request.form['sessionID']

            # TODO: The sessionID should probably be sanitized

            # Check our generated directory for the submitted session ID
            if os.path.isdir(cwd + '/static/generated/' + sessionID):
                musicPath = '/static/generated/' + sessionID + '/output.wav'
                dataPath = cwd + '/static/generated/' + sessionID + '/data.csv'
                queryPath = cwd + '/static/generated/' + sessionID + '/query.txt'

                # Read the query to produce the hyperlink to Chronograf
                queryFile = open(queryPath, 'r')
                query = queryFile.read()

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

                influx.close()
                return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs,
                                       legend=legend, labels=labels, values=values, music=True, musicPath=musicPath,
                                       sessionID=sessionID, amountPoints=amountPoints, query=query)

            else:
                flash('A session with an ID of \'' + sessionID + '\' was not found.', 'danger')

    influx.close()
    return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs, music=False)
