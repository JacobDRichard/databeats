from flask import Flask


def create_app():
    appl = Flask(__name__)

    with appl.app_context():
        from home import home
        from data import data
        from database import database
        from sonify import sonify

        appl.register_blueprint(home.home_bp, url_prefix='/')
        appl.register_blueprint(data.data_bp, url_prefix='/')
        appl.register_blueprint(database.database_bp, url_prefix='/')
        appl.register_blueprint(sonify.sonify_bp, url_prefix='/')

        return appl


app = create_app()
app.secret_key = 'secret'

if __name__ == '__main__':
    app.jinja_env.add_extension('jinja2.ext.do')
    app.run(host='localhost')
