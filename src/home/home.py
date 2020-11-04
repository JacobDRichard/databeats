from flask import Blueprint, render_template

home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/home/static'
)


@home_bp.route('/', methods=['GET'])
def home():
    return render_template('home.html')
