from flask import Blueprint, render_template

storage_bp = Blueprint(
    'storage_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/storage/static'
)


@storage_bp.route('/storage', methods=['GET'])
def storage():
    return render_template('storage.html')
