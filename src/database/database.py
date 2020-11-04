from flask import Blueprint, request, abort
import itertools
from settings import settings

database_bp = Blueprint(
    'database_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@database_bp.route('/database/get_measurements')
def get_measurements():
    influx = settings.influxdb()
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


@database_bp.route('/database/get_series/get_tag_names')
def get_tag_names():
    influx = settings.influxdb()
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


@database_bp.route('/database/get_series/get_tag_values')
def get_tag_values():
    influx = settings.influxdb()
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


@database_bp.route('/database/get_series/get_fields')
def get_fields():
    influx = settings.influxdb()
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
