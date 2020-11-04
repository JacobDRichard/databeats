from influxdb import InfluxDBClient


def influxdb():
    return InfluxDBClient(host='influxdb', port=8086)
