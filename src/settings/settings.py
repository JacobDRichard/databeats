from influxdb import InfluxDBClient
from flask import Blueprint, render_template


settings_bp = Blueprint(
    'settings_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/settings/static'
)


def influxdb():
    return InfluxDBClient(host='influxdb', port=8086)


@settings_bp.route('/settings', methods=['GET'])
def settings():
    return render_template('settings.html')
