from flask import Blueprint, render_template, request, redirect, url_for, flash
import configparser
import os
import shutil

storage_bp = Blueprint(
    'storage_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/storage/static'
)


@storage_bp.route('/storage', methods=['GET', 'POST'])
def storage():
    # We need to walk the app/static/generated directory to fill the table
    cwd = os.getcwd()
    generatedDir = cwd + '/static/generated/'

    # Create our generated directory if it doesn't already exist
    if not os.path.isdir(generatedDir):
        os.mkdir(generatedDir)

    dirContents = os.listdir(generatedDir)

    if request.method == 'POST':
        button = request.form.get('action')
        action = button.split('_')

        if action[0] == 'view':
            return redirect(url_for('results_bp.results', uuid=action[1]))

        elif action[0] == 'schedule':
            print('schedule ' + action[1])

        elif action[0] == 'delete':
            shutil.rmtree(generatedDir + '/' + action[1])
            flash('Query \'' + action[1] + '\' was deleted successfully.', 'success')

    table = []
    for item in dirContents:
        if os.path.isdir(generatedDir + '/' + item):
            tableItem = []

            # Read the information file
            info = configparser.ConfigParser()
            info.read(generatedDir + '/' + item + '/information.ini')

            # Create the item list for the table list
            tableItem.append(item)
            # Make the shortened ID
            tableItem.append(item[0:4] + '...' + item[len(item) - 4: len(item)])

            # Time information
            # Keep track of the query type
            qType = info['Query']['type']
            tableItem.append(qType)
            if qType == 'Absolute':
                tableItem.append(info['Time']['start'] + ' to ' + info['Time']['end'])
            else:
                tableItem.append('Past ' + info['Time']['numpast'] + ' ' + info['Time']['pastx'] + ' (' + info['Time'][
                    'start'] + ' to ' + info['Time']['end'] + ')')
            tableItem.append(info['Time']['generated'])

            # Source information
            tableItem.append(info['Source']['database'])
            tableItem.append(info['Source']['measurement'])
            tableItem.append(info['Source']['field'])
            if info['Source']['tagname'] is not '':
                tableItem.append(info['Source']['tagname'] + '=' + info['Source']['tagvalue'])
            else:
                tableItem.append('N/A')
            if info['Source']['fieldfunction'] is not '':
                tableItem.append(info['Source']['fieldfunction'] + ' every ' + info['Source']['groupby'])
            else:
                tableItem.append('N/A')

            table.append(tableItem)

    return render_template('storage.html', table=table)
