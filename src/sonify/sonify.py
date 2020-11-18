from flask import Blueprint, render_template, request, flash, redirect, url_for
from settings import settings
import os
from os import listdir
from os.path import isfile, join
import subprocess
import uuid
from datetime import datetime, timedelta
import csv
from music21 import *
from dateutil.relativedelta import relativedelta
import configparser

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

    # Get the list of instruments that can be used
    instrumentDir = os.getcwd() + '/instruments/'
    instrumentList = [f.split('.')[0] for f in listdir(instrumentDir) if isfile(join(instrumentDir, f))]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'query':
            database = request.form['database']
            measurement = request.form['measurement']
            field = request.form['field']
            instrument = request.form['instrument']
            fieldFunction = request.form.get('fieldFunction', '')
            groupBy = request.form.get('groupBy', '')
            queryType = request.form.get('type', 'off')
            numPast = request.form['numPast']
            pastX = request.form['pastX']

            tagName = ''
            if 'tagName' in request.form:
                tagName = request.form['tagName']

            tagValue = ''
            if 'tagValue' in request.form:
                tagValue = request.form['tagValue']

            # Create the starting and ending datetime based on query type
            start = ''
            end = ''
            if queryType == 'on':
                # This is an absolute query
                datetimeStart = request.form['datetimeStart']
                datetimeEnd = request.form['datetimeEnd']

                # Check the submitted datetime data
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

                try:
                    end = datetime.strptime(datetimeEnd, '%Y-%m-%dT%H:%M:%S')

                except ValueError:
                    # Failed to parse, compatibility check across browsers, some do not include seconds
                    try:
                        end = datetime.strptime(datetimeEnd + ':00', '%Y-%m-%dT%H:%M:%S')

                    except ValueError:
                        # Unable to parse the submitted data, flash error
                        flash('Unable to parse the submitted end datetime.', 'danger')

                end = datetime.strftime(end, '%Y-%m-%dT%H:%M:%S') + 'Z'

            elif queryType == 'off':
                # This is a relative query
                now = datetime.now()
                end = datetime.now()
                now = now.replace(microsecond=0)

                if pastX == 'seconds':
                    now -= timedelta(seconds=int(numPast))
                elif pastX == 'minutes':
                    now -= timedelta(minutes=int(numPast))
                elif pastX == 'hours':
                    now -= timedelta(hours=int(numPast))
                elif pastX == 'days':
                    now -= timedelta(days=int(numPast))
                elif pastX == 'weeks':
                    now -= timedelta(weeks=int(numPast))
                elif pastX == 'months':
                    now -= relativedelta(months=-int(numPast))
                elif pastX == 'years':
                    now -= relativedelta(years=-int(numPast))

                start = datetime.strftime(now, '%Y-%m-%dT%H:%M:%S') + 'Z'
                end = datetime.strftime(end, '%Y-%m-%dT%H:%M:%S') + 'Z'

            print(start)
            print(end)

            tagSection = ''
            if tagName and tagValue is not '':
                tagSection = ' AND \"' + tagName + '\"=\'' + tagValue + '\''

            # Create query from submitted form data
            if fieldFunction is not '':
                query = 'SELECT ' + fieldFunction + '(\"' + field + '\") AS data FROM \"' + database + \
                        '\".\"autogen\".\"' + measurement + '\" WHERE time > \'' + start + '\' AND time < \'' + end + \
                        '\'' + tagSection + ' GROUP BY time(' + groupBy + ')'
            else:
                query = 'SELECT ' + field + ' AS data FROM \"' + database + '\".\"autogen\".\"' + measurement \
                        + '\" WHERE time > \'' + start + '\' AND time < \'' + end + '\'' + tagSection

            result = influx.query(query).raw

            resultDataList = result['series']

            if len(resultDataList):
                # Query returned data, generate random session ID
                sessionID = str(uuid.uuid4())

                # Grab minimum and maximum value for scaling
                resultDataRaw = resultDataList[0]['values']

                # Remove all None values
                resultData = []
                for point in resultDataRaw:
                    if point[1] is not None:
                        resultData.append(point)

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
                # fluidsynth -ni -F output.wav -r 44100 Piano.sf2 test.midi
                outName = cwd + '/static/generated/' + sessionID + '/output.wav'
                midiName = 'midi_' + sessionID + '.midi'
                instrumentFile = cwd + '/instruments/' + instrument + '.sf2'
                subprocess.call(['fluidsynth', '-ni', '-F', outName, '-r', '44100', instrumentFile, midiName])

                # Get path of the generated music
                musicPath = '/static/generated/' + sessionID + '/output.wav'

                # Save queried data into file for when the user looks up the session ID
                with open(cwd + '/static/generated/' + sessionID + '/data.csv', mode='w') as dataCSV:
                    columns = ['time', measurement + '.' + field]
                    writer = csv.DictWriter(dataCSV, fieldnames=columns)

                    writer.writeheader()
                    for point in resultData:
                        writer.writerow({'time': point[0], measurement + '.' + field: point[1]})

                # Save information about this query
                config = configparser.ConfigParser()

                if queryType == 'on':
                    qType = 'Absolute'
                else:
                    qType = 'Relative'

                config['Query'] = {'Type': qType,
                                   'Query': query}

                config['Source'] = {'Database': database,
                                    'Measurement': measurement,
                                    'Field': field,
                                    'TagName': tagName,
                                    'TagValue': tagValue,
                                    'Instrument': instrument,
                                    'FieldFunction': fieldFunction,
                                    'GroupBy': groupBy}

                if qType == 'Absolute':
                    config['Time'] = {'Start': start,
                                      'End': end}
                else:
                    config['Time'] = {'numPast': numPast,
                                      'pastX': pastX}

                with open(cwd + '/static/generated/' + sessionID + '/information.ini', 'w') as file:
                    config.write(file)

                # Cleanup old files
                os.remove(cwd + '/midi_' + sessionID + '.midi')

                influx.close()
                # Redirect to the results page
                return redirect(url_for('results_bp.results', uuid=sessionID))

            else:
                flash('Query did not return any data, please try again.', 'danger')

    influx.close()
    return render_template('sonify.html', datetimeS=datetimeS, datetimeE=datetimeE, list_dbs=list_dbs, instrumentList=instrumentList)
