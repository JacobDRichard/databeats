from flask import Blueprint, render_template, request, flash, redirect, url_for
from settings import settings
import os
from datetime import datetime, timedelta
from random import randint
import csv
from werkzeug.utils import secure_filename

data_bp = Blueprint(
    'data_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/data/static'
)


@data_bp.route('/data', methods=['GET', 'POST'])
def data():
    influx = settings.influxdb()
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

                influx.close()
                flash('Database \'' + dbName + '\' was created successfully.', 'success')
                return redirect(url_for('data_bp.data'))

            else:
                flash('Database \'' + dbName + '\' was not created because it already exists.', 'danger')

        elif action[0] == 'delete':
            # In case the name had dashes in it
            databaseName = ''
            for i in range(len(action)):
                if i is 0:
                    continue

                databaseName += action[i]

                if i is not len(action) - 1:
                    databaseName += '-'

            # Delete the database on InfluxDB
            influx.drop_database(databaseName)

            influx.close()
            flash('Database \'' + databaseName + '\' was deleted successfully.', 'success')
            return redirect(url_for('data_bp.data'))
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
        elif action[0] == 'upload':
            # Retrieve and save file
            file = request.files['uploadFile']
            file.save(secure_filename(file.filename))

            # Parse uploaded file
            uploadData = []
            with open(file.filename, 'r') as uploadFile:
                reader = csv.reader(uploadFile)

                # Extract measurement and field name
                dataColumn = next(reader)
                measurement = dataColumn[1].split('.')[0]
                field = dataColumn[1].split('.')[1]

                # Parse data and create JSON list for DB write
                for line in reader:
                    dataJSON = {
                        'measurement': measurement,
                        'time': line[0],
                        'fields': {
                            field: int(line[1])
                        }
                    }
                    uploadData.append(dataJSON)

            # Remove uploaded file
            cwd = os.getcwd()
            os.remove(cwd + '/' + file.filename)

            # Swap to selected database
            database = request.form['uploadDatabase']
            influx.switch_database(database)

            # Write data to the database
            result = influx.write_points(uploadData)

            if result:
                flash('Submitted \'' + file.filename + '\' file time series data to database \'' + database +
                      '\' successfully.', 'success')
            else:
                flash('Failed to submit uploaded time series data to database \'' + database + '\'.',
                      'danger')

    influx.close()
    return render_template('data.html', datetimeF=datetimeF, tuples_dbs=tuples_dbs, list_dbs=list_dbs)
