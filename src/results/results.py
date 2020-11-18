from flask import Blueprint, render_template

results_bp = Blueprint(
    'results_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/results/static'
)


@results_bp.route('/results', methods=['GET', 'POST'])
def results_base():
    return render_template('results.html', music=False)


@results_bp.route('/results/<uuid>', methods=['GET'])
def results(uuid):
    print('.')
