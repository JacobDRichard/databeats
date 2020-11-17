from influxdb import InfluxDBClient
from flask import Blueprint, render_template, request, flash
import configparser
import os

settings_bp = Blueprint(
    'settings_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/settings/static'
)

readSettings = False
# Default settings
host = 'influxdb'
port = 8086


def influxdb():
    global readSettings, host, port

    if not readSettings:
        # Open the settings file
        config = configparser.ConfigParser()
        cwd = os.getcwd()
        config.read(cwd + '/settings.ini')

        # Read the current settings
        host = config['InfluxDB']['Host']
        port = config['InfluxDB']['Port']

        readSettings = True

    return InfluxDBClient(host=host, port=port)


@settings_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    global host, port

    # Open the settings file
    config = configparser.ConfigParser()
    cwd = os.getcwd()
    config.read(cwd + '/settings.ini')

    # Read the current settings
    readHost = config['InfluxDB']['Host']
    readPort = config['InfluxDB']['Port']

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'apply':
            inputHost = request.form['dbHost']
            inputPort = request.form['dbPort']

            # Set the global host and port to the inputted ones
            host = inputHost
            port = inputPort

            # Write the new settings to the settings file
            config['InfluxDB'] = {'Host': inputHost,
                                  'Port': inputPort}

            with open(cwd + '/settings.ini', 'w') as file:
                config.write(file)

            flash('The settings were applied successfully', 'success')
            return render_template('settings.html', host=inputHost, port=inputPort)

    return render_template('settings.html', host=readHost, port=readPort)
