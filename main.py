from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import datetime
from flask_cors import CORS
import inspect
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb+srv://ziyodullasodiqov0105:aOP6DXujBayzD1Km@zsm.5so3iiu.mongodb.net/?retryWrites=true&w=majority&appName=ZSM')
db = client['university_db']
admins = db['admins']
unv_drs = db['unv_drs']
teachers = db['teachers']
phd_records = db['phd_records']
projects = db['projects']
contracts = db['contracts']
pending_projects = db['pending_projects']
result_views = db['result_views']
doktorants = db['doktorants']
students = db['students']
articles = db['articles']
patents = db['patents']
monografiyas = db['monografiyas']
operations = db['operations']

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to log operations
def log_operation(entity, operation, user_id):
    operations.insert_one({
        'entity': entity,
        'operation': operation,
        'user_id': str(user_id),
        'timestamp': datetime.datetime.utcnow()
    })

# ADMIN Endpoints
@app.route('/admin', methods=['POST'])
def create_admin():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    if admins.find_one({'username': data['username']}):
        return jsonify({'error': 'Username already exists'}), 400
    admin_id = admins.insert_one({
        'username': data['username'],
        'password': data['password']
    }).inserted_id
    return jsonify({'message': 'Admin created', 'id': str(admin_id)}), 201

@app.route('/admin/<id>', methods=['PUT'])
def update_admin(id):
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    result = admins.update_one(
        {'_id': ObjectId(id)},
        {'$set': {'username': data['username'], 'password': data['password']}}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Admin not found'}), 404
    log_operation('admin', 'PUT', id)
    return jsonify({'message': 'Admin updated'}), 200

@app.route('/admin/<id>', methods=['DELETE'])
def delete_admin(id):
    result = admins.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Admin not found'}), 404
    log_operation('admin', 'DELETE', id)
    return jsonify({'message': 'Admin deleted'}), 200

# UNV_DR Endpoints
@app.route('/unv_dr', methods=['POST'])
def create_unv_dr():
    data = request.get_json()
    required_fields = ['name', 'surname', 'kafeteria_name', 'username', 'password']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    if unv_drs.find_one({'username': data['username']}):
        return jsonify({'error': 'Username already exists'}), 400
    unv_dr_id = unv_drs.insert_one(data).inserted_id
    return jsonify({'message': 'UNV_DR created', 'id': str(unv_dr_id)}), 201

@app.route('/unv_dr/<id>', methods=['PUT'])
def update_unv_dr(id):
    data = request.get_json()
    required_fields = ['name', 'surname', 'kafeteria_name', 'username', 'password']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    result = unv_drs.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'UNV_DR not found'}), 404
    log_operation('unv_dr', 'PUT', id)
    return jsonify({'message': 'UNV_DR updated'}), 200

@app.route('/unv_dr/<id>', methods=['DELETE'])
def delete_unv_dr(id):
    result = unv_drs.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'UNV_DR not found'}), 404
    # Delete associated data
    teachers.delete_many({'unv_dr_id': ObjectId(id)})
    phd_records.delete_many({'unv_dr_id': ObjectId(id)})
    projects.delete_many({'unv_dr_id': ObjectId(id)})
    contracts.delete_many({'unv_dr_id': ObjectId(id)})
    pending_projects.delete_many({'unv_dr_id': ObjectId(id)})
    result_views.delete_many({'unv_dr_id': ObjectId(id)})
    doktorants.delete_many({'unv_dr_id': ObjectId(id)})
    log_operation('unv_dr', 'DELETE', id)
    return jsonify({'message': 'UNV_DR and associated data deleted'}), 200

# TEACHER Endpoints
@app.route('/teacher', methods=['POST'])
def create_teacher():
    data = request.get_json()
    required_fields = ['name', 'surname', 'degree', 'username', 'password', 'position', 'work_hours', 'academic_level', 'diploma_id', 'diploma_date', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    if teachers.find_one({'username': data['username']}):
        return jsonify({'error': 'Username already exists'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    teacher_id = teachers.insert_one(data).inserted_id
    log_operation('teacher', 'POST', teacher_id)
    return jsonify({'message': 'Teacher created', 'id': str(teacher_id)}), 201

@app.route('/teacher/<id>', methods=['PUT'])
def update_teacher(id):
    data = request.get_json()
    required_fields = ['name', 'surname', 'degree', 'username', 'password', 'position', 'work_hours', 'academic_level', 'diploma_id', 'diploma_date', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = teachers.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Teacher not found'}), 404
    log_operation('teacher', 'PUT', id)
    return jsonify({'message': 'Teacher updated'}), 200

@app.route('/teacher/<id>', methods=['DELETE'])
def delete_teacher(id):
    result = teachers.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Teacher not found'}), 404
    # Delete associated data
    students.delete_many({'teacher_id': ObjectId(id)})
    articles.delete_many({'teacher_id': ObjectId(id)})
    patents.delete_many({'teacher_id': ObjectId(id)})
    monografiyas.delete_many({'teacher_id': ObjectId(id)})
    log_operation('teacher', 'DELETE', id)
    return jsonify({'message': 'Teacher deleted'}), 200

# PHD_RECORD Endpoints
@app.route('/phd_record', methods=['POST'])
def create_phd_record():
    data = request.get_json()
    required_fields = ['name', 'surname', 'position', 'phd_dsc', 'phd_dsc_date', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    phd_record_id = phd_records.insert_one(data).inserted_id
    log_operation('phd_record', 'POST', phd_record_id)
    return jsonify({'message': 'PhD record created', 'id': str(phd_record_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/phd_records', methods=['GET'])
def view_phd_records_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        phd_record_list = list(phd_records.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'name': 1, 'surname': 1, 'position': 1, 'phd_dsc': 1, 'phd_dsc_date': 1, 'unv_dr_id': 1}
        ))
        if not phd_record_list:
            phd_record_list = list(phd_records.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'name': 1, 'surname': 1, 'position': 1, 'phd_dsc': 1, 'phd_dsc_date': 1, 'unv_dr_id': 1}
            ))
        for record in phd_record_list:
            record['_id'] = str(record['_id'])
            record['unv_dr_id'] = str(record['unv_dr_id'])
        return jsonify({'phd_records': phd_record_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/phd_record/<id>', methods=['GET'])
def get_phd_record(id):
    try:
        record = phd_records.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'name': 1, 'surname': 1, 'position': 1, 'phd_dsc': 1, 'phd_dsc_date': 1, 'unv_dr_id': 1}
        )
        if not record:
            return jsonify({'error': 'PhD record not found'}), 404
        record['_id'] = str(record['_id'])
        record['unv_dr_id'] = str(record['unv_dr_id'])
        return jsonify({'phd_record': record}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/phd_record/<id>', methods=['PUT'])
def update_phd_record(id):
    data = request.get_json()
    required_fields = ['name', 'surname', 'position', 'phd_dsc', 'phd_dsc_date', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = phd_records.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'PhD record not found'}), 404
    log_operation('phd_record', 'PUT', id)
    return jsonify({'message': 'PhD record updated'}), 200

@app.route('/phd_record/<id>', methods=['DELETE'])
def delete_phd_record(id):
    result = phd_records.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'PhD record not found'}), 404
    log_operation('phd_record', 'DELETE', id)
    return jsonify({'message': 'PhD record deleted'}), 200

# PROJECT Endpoints
@app.route('/project', methods=['POST'])
def create_project():
    data = request.get_json()
    required_fields = ['project_paragraph', 'project_price', 'project_author', 'project_status', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    project_id = projects.insert_one(data).inserted_id
    log_operation('project', 'POST', project_id)
    return jsonify({'message': 'Project created', 'id': str(project_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/projects', methods=['GET'])
def view_projects_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        project_list = list(projects.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'project_paragraph': 1, 'project_price': 1, 'project_author': 1, 'project_author_name': 1, 'project_status': 1, 'unv_dr_id': 1}
        ))
        if not project_list:
            project_list = list(projects.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'project_paragraph': 1, 'project_price': 1, 'project_author': 1, 'project_author_name': 1, 'project_status': 1, 'unv_dr_id': 1}
            ))
        for project in project_list:
            project['_id'] = str(project['_id'])
            project['unv_dr_id'] = str(project['unv_dr_id'])
        return jsonify({'projects': project_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/project/<id>', methods=['GET'])
def get_project(id):
    try:
        project = projects.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'project_paragraph': 1, 'project_price': 1, 'project_author': 1, 'project_author_name': 1, 'project_status': 1, 'unv_dr_id': 1}
        )
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        project['_id'] = str(project['_id'])
        project['unv_dr_id'] = str(project['unv_dr_id'])
        return jsonify({'project': project}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/project/<id>', methods=['PUT'])
def update_project(id):
    data = request.get_json()
    required_fields = ['project_paragraph', 'project_price', 'project_author', 'project_status', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = projects.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Project not found'}), 404
    log_operation('project', 'PUT', id)
    return jsonify({'message': 'Project updated'}), 200

@app.route('/project/<id>', methods=['DELETE'])
def delete_project(id):
    result = projects.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Project not found'}), 404
    log_operation('project', 'DELETE', id)
    return jsonify({'message': 'Project deleted'}), 200

# CONTRACT Endpoints
@app.route('/contract', methods=['POST'])
def create_contract():
    data = request.get_json()
    required_fields = ['contract_name', 'contract_title', 'contract_price', 'contract_company', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    contract_id = contracts.insert_one(data).inserted_id
    log_operation('contract', 'POST', contract_id)
    return jsonify({'message': 'Contract created', 'id': str(contract_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/contracts', methods=['GET'])
def view_contracts_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        contract_list = list(contracts.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'contract_name': 1, 'contract_title': 1, 'contract_price': 1, 'contract_company': 1, 'unv_dr_id': 1}
        ))
        if not contract_list:
            contract_list = list(contracts.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'contract_name': 1, 'contract_title': 1, 'contract_price': 1, 'contract_company': 1, 'unv_dr_id': 1}
            ))
        for contract in contract_list:
            contract['_id'] = str(contract['_id'])
            contract['unv_dr_id'] = str(contract['unv_dr_id'])
        return jsonify({'contracts': contract_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/contract/<id>', methods=['GET'])
def get_contract(id):
    try:
        contract = contracts.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'contract_name': 1, 'contract_title': 1, 'contract_price': 1, 'contract_company': 1, 'unv_dr_id': 1}
        )
        if not contract:
            return jsonify({'error': 'Contract not found'}), 404
        contract['_id'] = str(contract['_id'])
        contract['unv_dr_id'] = str(contract['unv_dr_id'])
        return jsonify({'contract': contract}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/contract/<id>', methods=['PUT'])
def update_contract(id):
    data = request.get_json()
    required_fields = ['contract_name', 'contract_title', 'contract_price', 'contract_company', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = contracts.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Contract not found'}), 404
    log_operation('contract', 'PUT', id)
    return jsonify({'message': 'Contract updated'}), 200

@app.route('/contract/<id>', methods=['DELETE'])
def delete_contract(id):
    result = contracts.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Contract not found'}), 404
    log_operation('contract', 'DELETE', id)
    return jsonify({'message': 'Contract deleted'}), 200

# PENDING_PROJECT Endpoints
@app.route('/pending_project', methods=['POST'])
def create_pending_project():
    data = request.get_json()
    required_fields = ['pending_project_name', 'pending_project_price', 'pending_project_author', 'pending_achieved_result', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    pending_project_id = pending_projects.insert_one(data).inserted_id
    log_operation('pending_project', 'POST', pending_project_id)
    return jsonify({'message': 'Pending project created', 'id': str(pending_project_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/pending_projects', methods=['GET'])
def view_pending_projects_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        pending_project_list = list(pending_projects.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'pending_project_name': 1, 'pending_project_price': 1, 'pending_project_author': 1, 'pending_achieved_result': 1, 'unv_dr_id': 1}
        ))
        if not pending_project_list:
            pending_project_list = list(pending_projects.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'pending_project_name': 1, 'pending_project_price': 1, 'pending_project_author': 1, 'pending_achieved_result': 1, 'unv_dr_id': 1}
            ))
        for record in pending_project_list:
            record['_id'] = str(record['_id'])
            record['unv_dr_id'] = str(record['unv_dr_id'])
        return jsonify({'pending_projects': pending_project_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/pending_project/<id>', methods=['GET'])
def get_pending_project(id):
    try:
        pending_project = pending_projects.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'pending_project_name': 1, 'pending_project_price': 1, 'pending_project_author': 1, 'pending_achieved_result': 1, 'unv_dr_id': 1}
        )
        if not pending_project:
            return jsonify({'error': 'Pending project not found'}), 404
        pending_project['_id'] = str(pending_project['_id'])
        pending_project['unv_dr_id'] = str(pending_project['unv_dr_id'])
        return jsonify({'pending_project': pending_project}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/pending_project/<id>', methods=['PUT'])
def update_pending_project(id):
    data = request.get_json()
    required_fields = ['pending_project_name', 'pending_project_price', 'pending_project_author', 'pending_achieved_result', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = pending_projects.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Pending project not found'}), 404
    log_operation('pending_project', 'PUT', id)
    return jsonify({'message': 'Pending project updated'}), 200

@app.route('/pending_project/<id>', methods=['DELETE'])
def delete_pending_project(id):
    result = pending_projects.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Pending project not found'}), 404
    log_operation('pending_project', 'DELETE', id)
    return jsonify({'message': 'Pending project deleted'}), 200

# RESULT_VIEW Endpoints
@app.route('/result_view', methods=['POST'])
def create_result_view():
    data = request.get_json()
    required_fields = ['result_view', 'company_name', 'date', 'result_title', 'achieved_result', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result_view_id = result_views.insert_one(data).inserted_id
    log_operation('result_view', 'POST', result_view_id)
    return jsonify({'message': 'Result view created', 'id': str(result_view_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/result_views', methods=['GET'])
def view_result_views_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        result_view_list = list(result_views.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'result_view': 1, 'company_name': 1, 'date': 1, 'result_title': 1, 'achieved_result': 1, 'unv_dr_id': 1}
        ))
        if not result_view_list:
            result_view_list = list(result_views.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'result_view': 1, 'company_name': 1, 'date': 1, 'result_title': 1, 'achieved_result': 1, 'unv_dr_id': 1}
            ))
        for record in result_view_list:
            record['_id'] = str(record['_id'])
            record['unv_dr_id'] = str(record['unv_dr_id'])
        return jsonify({'result_views': result_view_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/result_view/<id>', methods=['GET'])
def get_result_view(id):
    try:
        result_view = result_views.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'result_view': 1, 'company_name': 1, 'date': 1, 'result_title': 1, 'achieved_result': 1, 'unv_dr_id': 1}
        )
        if not result_view:
            return jsonify({'error': 'Result view not found'}), 404
        result_view['_id'] = str(result_view['_id'])
        result_view['unv_dr_id'] = str(result_view['unv_dr_id'])
        return jsonify({'result_view': result_view}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/result_view/<id>', methods=['PUT'])
def update_result_view(id):
    data = request.get_json()
    required_fields = ['result_view', 'company_name', 'date', 'result_title', 'achieved_result', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = result_views.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Result view not found'}), 404
    log_operation('result_view', 'PUT', id)
    return jsonify({'message': 'Result view updated'}), 200

@app.route('/result_view/<id>', methods=['DELETE'])
def delete_result_view(id):
    result = result_views.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Result view not found'}), 404
    log_operation('result_view', 'DELETE', id)
    return jsonify({'message': 'Result view deleted'}), 200

# DOKTORANT Endpoints
@app.route('/doktorant', methods=['POST'])
def create_doktorant():
    data = request.get_json()
    required_fields = ['doktorants_name', 'doktorants_surname', 'doktorants_course', 'dissirtation_name', 'scientific_supervisor', 'dissirtation_pending', 'dissertation_defense_plan', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    doktorant_id = doktorants.insert_one(data).inserted_id
    log_operation('doktorant', 'POST', doktorant_id)
    return jsonify({'message': 'Doktorant created', 'id': str(doktorant_id)}), 201

@app.route('/admin/unv_dr/<unv_dr_id>/doktorants', methods=['GET'])
def view_doktorants_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        doktorant_list = list(doktorants.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'doktorants_name': 1, 'doktorants_surname': 1, 'doktorants_course': 1, 'dissirtation_name': 1, 'scientific_supervisor': 1, 'dissirtation_pending': 1, 'dissertation_defense_plan': 1, 'unv_dr_id': 1}
        ))
        if not doktorant_list:
            doktorant_list = list(doktorants.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'doktorants_name': 1, 'doktorants_surname': 1, 'doktorants_course': 1, 'dissirtation_name': 1, 'scientific_supervisor': 1, 'dissirtation_pending': 1, 'dissertation_defense_plan': 1, 'unv_dr_id': 1}
            ))
        for record in doktorant_list:
            record['_id'] = str(record['_id'])
            record['unv_dr_id'] = str(record['unv_dr_id'])
        return jsonify({'doktorants': doktorant_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doktorant/<id>', methods=['GET'])
def get_doktorant(id):
    try:
        doktorant = doktorants.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'doktorants_name': 1, 'doktorants_surname': 1, 'doktorants_course': 1, 'dissirtation_name': 1, 'scientific_supervisor': 1, 'dissirtation_pending': 1, 'dissertation_defense_plan': 1, 'unv_dr_id': 1}
        )
        if not doktorant:
            return jsonify({'error': 'Doktorant not found'}), 404
        doktorant['_id'] = str(doktorant['_id'])
        doktorant['unv_dr_id'] = str(doktorant['unv_dr_id'])
        return jsonify({'doktorant': doktorant}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/doktorant/<id>', methods=['PUT'])
def update_doktorant(id):
    data = request.get_json()
    required_fields = ['doktorants_name', 'doktorants_surname', 'doktorants_course', 'dissirtation_name', 'scientific_supervisor', 'dissirtation_pending', 'dissertation_defense_plan', 'unv_dr_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
            return jsonify({'error': 'UNV_DR not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid unv_dr_id: {str(e)}'}), 400
    result = doktorants.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Doktorant not found'}), 404
    log_operation('doktorant', 'PUT', id)
    return jsonify({'message': 'Doktorant updated'}), 200

@app.route('/doktorant/<id>', methods=['DELETE'])
def delete_doktorant(id):
    result = doktorants.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Doktorant not found'}), 404
    log_operation('doktorant', 'DELETE', id)
    return jsonify({'message': 'Doktorant deleted'}), 200

# STUDENT Endpoints
@app.route('/student', methods=['POST'])
def create_student():
    try:
        data = request.get_json()
        required_fields = ['student_name', 'course_name', 'group_name', 'course_number', 'kafeteria_name', 'curator_name', 'teacher_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        data['teacher_id'] = ObjectId(data['teacher_id'])
        
        if not teachers.find_one({'_id': data['teacher_id']}):
            return jsonify({'error': 'Teacher not found'}), 404
        
        student_id = students.insert_one(data).inserted_id
        return jsonify({'message': 'Student created', '_id': str(student_id)}), 201
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/teacher/<teacher_id>/students', methods=['GET'])
def view_students_by_teacher(teacher_id):
    try:
        print(f"Received teacher_id: {teacher_id}")  # Debug log
        
        # Check if teacher exists
        teacher = teachers.find_one({'_id': ObjectId(teacher_id)})
        if not teacher:
            print("Teacher not found")  # Debug log
            return jsonify({'error': 'Teacher not found'}), 404
        
        print("Teacher exists, searching for students...")  # Debug log
        
        # Debug: Print all students with this teacher_id in both formats
        students_str = list(students.find({'teacher_id': teacher_id}))
        students_objid = list(students.find({'teacher_id': ObjectId(teacher_id)}))
        
        print(f"Students found with string teacher_id: {len(students_str)}")
        print(f"Students found with ObjectId teacher_id: {len(students_objid)}")
        
        # Try both query formats
        query = {
            '$or': [
                {'teacher_id': ObjectId(teacher_id)},
                {'teacher_id': teacher_id}
            ]
        }
        
        student_list = list(students.find(
            query,
            {'_id': 1, 'student_name': 1, 'course_name': 1, 'group_name': 1, 
             'course_number': 1, 'kafeteria_name': 1, 'curator_name': 1, 'teacher_id': 1}
        ))
        
        print(f"Total students found: {len(student_list)}")  # Debug log
        
        for record in student_list:
            record['_id'] = str(record['_id'])
            record['teacher_id'] = str(record['teacher_id'])
            
        return jsonify({'students': student_list}), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug log
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/student/<id>', methods=['GET'])
def get_student(id):
    try:
        student = students.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'student_name': 1, 'course_name': 1, 'group_name': 1, 'course_number': 1, 'kafeteria_name': 1, 'curator_name': 1, 'teacher_id': 1}
        )
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        student['_id'] = str(student['_id'])
        student['teacher_id'] = str(student['teacher_id'])
        return jsonify({'student': student}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/student/<id>', methods=['PUT'])
def update_student(id):
    data = request.get_json()
    required_fields = ['student_name', 'course_name', 'group_name', 'course_number', 'kafeteria_name', 'curator_name', 'teacher_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    result = students.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Student not found'}), 404
    log_operation('student', 'PUT', id)
    return jsonify({'message': 'Student updated'}), 200

@app.route('/student/<id>', methods=['DELETE'])
def delete_student(id):
    result = students.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Student not found'}), 404
    log_operation('student', 'DELETE', id)
    return jsonify({'message': 'Student deleted'}), 200

# ARTICLE Endpoints
@app.route('/article', methods=['POST'])
def create_article():
    if 'article_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['article_file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: pdf, doc, docx'}), 400
    data = request.form.to_dict()
    required_fields = ['student_name_for_article', 'article_full_title', 'article_authors', 'journal_name', 'teacher_id']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    article_data = {
        'student_name': data['student_name_for_article'],
        'article_file_path': file_path,
        'article_title': data['article_full_title'],
        'authors': data['article_authors'],
        'journal_name': data['journal_name'],
        'teacher_id': data['teacher_id']
    }
    article_id = articles.insert_one(article_data).inserted_id
    log_operation('article', 'POST', article_id)
    return jsonify({'message': 'Article created', 'id': str(article_id)}), 201

@app.route('/teacher/<teacher_id>/articles', methods=['GET'])
def view_articles_by_teacher(teacher_id):
    try:
        if not teachers.find_one({'_id': ObjectId(teacher_id)}):
            return jsonify({'error': 'Teacher not found'}), 404
        article_list = list(articles.find(
            {'teacher_id': ObjectId(teacher_id)},
            {'_id': 1, 'student_name': 1, 'article_file_path': 1, 'article_title': 1, 'authors': 1, 'journal_name': 1, 'teacher_id': 1}
        ))
        for record in article_list:
            record['_id'] = str(record['_id'])
            record['teacher_id'] = str(record['teacher_id'])
        return jsonify({'articles': article_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/article/<id>', methods=['GET'])
def get_article(id):
    try:
        article = articles.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'student_name': 1, 'article_file_path': 1, 'article_title': 1, 'authors': 1, 'journal_name': 1, 'teacher_id': 1}
        )
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        article['_id'] = str(article['_id'])
        article['teacher_id'] = str(article['teacher_id'])
        return jsonify({'article': article}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/article/<id>', methods=['PUT'])
def update_article(id):
    data = request.form.to_dict()
    required_fields = ['student_name', 'article_title', 'authors', 'journal_name', 'teacher_id']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    update_data = {
        'student_name': data['student_name'],
        'article_title': data['article_title'],
        'authors': data['authors'],
        'journal_name': data['journal_name'],
        'teacher_id': data['teacher_id']
    }
    if 'article_file' in request.files:
        file = request.files['article_file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            update_data['article_file_path'] = file_path
    result = articles.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Article not found'}), 404
    log_operation('article', 'PUT', id)
    return jsonify({'message': 'Article updated'}), 200

@app.route('/article/<id>', methods=['DELETE'])
def delete_article(id):
    result = articles.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Article not found'}), 404
    log_operation('article', 'DELETE', id)
    return jsonify({'message': 'Article deleted'}), 200

# PATENT Endpoints
@app.route('/patent', methods=['POST'])
def create_patent():
    data = request.get_json()
    required_fields = ['patentsId', 'authors', 'patent_date', 'teacher_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    patent_id = patents.insert_one(data).inserted_id
    log_operation('patent', 'POST', patent_id)
    return jsonify({'message': 'Patent created', 'id': str(patent_id)}), 201

@app.route('/teacher/<teacher_id>/patents', methods=['GET'])
def view_patents_by_teacher(teacher_id):
    try:
        if not teachers.find_one({'_id': ObjectId(teacher_id)}):
            return jsonify({'error': 'Teacher not found'}), 404
        patent_list = list(patents.find(
            {'teacher_id': ObjectId(teacher_id)},
            {'_id': 1, 'patentsId': 1, 'authors': 1, 'patent_date': 1, 'teacher_id': 1}
        ))
        for record in patent_list:
            record['_id'] = str(record['_id'])
            record['teacher_id'] = str(record['teacher_id'])
        return jsonify({'patents': patent_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/patent/<id>', methods=['GET'])
def get_patent(id):
    try:
        patent = patents.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'patentsId': 1, 'authors': 1, 'patent_date': 1, 'teacher_id': 1}
        )
        if not patent:
            return jsonify({'error': 'Patent not found'}), 404
        patent['_id'] = str(patent['_id'])
        patent['teacher_id'] = str(patent['teacher_id'])
        return jsonify({'patent': patent}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/patent/<id>', methods=['PUT'])
def update_patent(id):
    data = request.get_json()
    required_fields = ['patentsId', 'authors', 'patent_date', 'teacher_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    result = patents.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Patent not found'}), 404
    log_operation('patent', 'PUT', id)
    return jsonify({'message': 'Patent updated'}), 200

@app.route('/patent/<id>', methods=['DELETE'])
def delete_patent(id):
    result = patents.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Patent not found'}), 404
    log_operation('patent', 'DELETE', id)
    return jsonify({'message': 'Patent deleted'}), 200

# MONOGRAFIYA Endpoints
@app.route('/monografiya', methods=['POST'])
def create_monografiya():
    data = request.get_json()
    required_fields = ['author_name', 'Monografiya_name', 'monografiya_date', 'teacher_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    monografiya_id = monografiyas.insert_one(data).inserted_id
    log_operation('monografiya', 'POST', monografiya_id)
    return jsonify({'message': 'Monografiya created', 'id': str(monografiya_id)}), 201

@app.route('/teacher/<teacher_id>/monografiyas', methods=['GET'])
def view_monografiyas_by_teacher(teacher_id):
    try:
        if not teachers.find_one({'_id': ObjectId(teacher_id)}):
            return jsonify({'error': 'Teacher not found'}), 404
        monografiya_list = list(monografiyas.find(
            {'teacher_id': ObjectId(teacher_id)},
            {'_id': 1, 'author_name': 1, 'Monografiya_name': 1, 'monografiya_date': 1, 'teacher_id': 1}
        ))
        for record in monografiya_list:
            record['_id'] = str(record['_id'])
            record['teacher_id'] = str(record['teacher_id'])
        return jsonify({'monografiyas': monografiya_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/monografiya/<id>', methods=['GET'])
def get_monografiya(id):
    try:
        monografiya = monografiyas.find_one(
            {'_id': ObjectId(id)},
            {'_id': 1, 'author_name': 1, 'Monografiya_name': 1, 'monografiya_date': 1, 'teacher_id': 1}
        )
        if not monografiya:
            return jsonify({'error': 'Monografiya not found'}), 404
        monografiya['_id'] = str(monografiya['_id'])
        monografiya['teacher_id'] = str(monografiya['teacher_id'])
        return jsonify({'monografiya': monografiya}), 200
    except Exception as e:
        return jsonify({'error': f'Invalid ID: {str(e)}'}), 400

@app.route('/monografiya/<id>', methods=['PUT'])
def update_monografiya(id):
    data = request.get_json()
    required_fields = ['author_name', 'Monografiya_name', 'monografiya_date', 'teacher_id']
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
    try:
        if not teachers.find_one({'_id': ObjectId(data['teacher_id'])}):
            return jsonify({'error': 'Teacher not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Invalid teacher_id: {str(e)}'}), 400
    result = monografiyas.update_one(
        {'_id': ObjectId(id)},
        {'$set': data}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Monografiya not found'}), 404
    log_operation('monografiya', 'PUT', id)
    return jsonify({'message': 'Monografiya updated'}), 200

@app.route('/monografiya/<id>', methods=['DELETE'])
def delete_monografiya(id):
    result = monografiyas.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Monografiya not found'}), 404
    log_operation('monografiya', 'DELETE', id)
    return jsonify({'message': 'Monografiya deleted'}), 200

# Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = admins.find_one({'username': data['username'], 'password': data['password']})
    if user:
        return jsonify({'message': 'Admin logged in', 'role': 'admin', 'id': str(user['_id'])}), 200
    
    user = unv_drs.find_one({'username': data['username'], 'password': data['password']})
    if user:
        return jsonify({'message': 'UNV_DR logged in', 'username': data['username'], 'role': 'unv_dr', 'id': str(user['_id'])}), 200
    
    user = teachers.find_one({'username': data['username'], 'password': data['password']})
    if user:
        return jsonify({'message': 'Teacher logged in', 'role': 'teacher', 'id': str(user['_id'])}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Admin View Operations and Teachers
@app.route('/admin/operations', methods=['GET'])
def view_operations():
    ops = list(operations.find({}, {'_id': 0, 'entity': 1, 'operation': 1, 'user_id': 1, 'timestamp': 1}))
    return jsonify({'operations': ops}), 200

@app.route('/health')
def health_check():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            try:
                view_func = app.view_functions[rule.endpoint]
                routes.append({
                    "route": str(rule),
                    "endpoint": rule.endpoint,
                    "function": view_func.__name__,
                    "module": inspect.getmodule(view_func).__name__ if inspect.getmodule(view_func) else None,
                    "status": "available"
                })
            except Exception as e:
                routes.append({
                    "route": str(rule),
                    "endpoint": rule.endpoint,
                    "error": str(e),
                    "status": "unavailable"
                })
    return jsonify({
        "status": "healthy",
        "routes": routes
    }), 200

@app.route('/unv_dr', methods=['GET'])
def get_all_unv_drs():
    unv_dr_list = list(unv_drs.find({}, {'_id': 1, 'name': 1, 'surname': 1, 'kafeteria_name': 1, 'username': 1, 'password': 1}))
    if not unv_dr_list:
        return jsonify({'message': 'No UNV_DRs found', 'unv_drs': []}), 200
    for unv_dr in unv_dr_list:
        unv_dr['_id'] = str(unv_dr['_id'])
    return jsonify({'unv_drs': unv_dr_list}), 200

@app.route('/admin/unv_dr/<unv_dr_id>/teachers', methods=['GET'])
def view_teachers_by_unv_dr(unv_dr_id):
    try:
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        teacher_list = list(teachers.find(
            {'unv_dr_id': ObjectId(unv_dr_id)},
            {'_id': 1, 'name': 1, 'surname': 1, 'degree': 1, 'username': 1, 'password': 1, 'position': 1, 'work_hours': 1, 'academic_level': 1, 'diploma_id': 1, 'diploma_date': 1}
        ))
        if not teacher_list:
            teacher_list = list(teachers.find(
                {'unv_dr_id': unv_dr_id},
                {'_id': 1, 'name': 1, 'surname': 1, 'degree': 1, 'username': 1, 'password': 1, 'position': 1, 'work_hours': 1, 'academic_level': 1, 'diploma_id': 1, 'diploma_date': 1}
            ))
        for teacher in teacher_list:
            teacher['_id'] = str(teacher['_id'])
        return jsonify({'teachers': teacher_list}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)