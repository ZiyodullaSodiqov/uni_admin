from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb+srv://ziyodullasodiqov0105:aOP6DXujBayzD1Km@zsm.5so3iiu.mongodb.net/?retryWrites=true&w=majority&appName=ZSM')
db = client['university_db']
admins = db['admins']
unv_drs = db['unv_drs']
teachers = db['teachers']
operations = db['operations']  

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
    # Delete associated teachers
    teachers.delete_many({'unv_dr_id': ObjectId(id)})
    log_operation('unv_dr', 'DELETE', id)
    return jsonify({'message': 'UNV_DR and associated teachers deleted'}), 200

# TEACHER Endpoints
@app.route('/teacher', methods=['POST'])
def create_teacher():
    data = request.get_json()
    required_fields = ['name', 'surname', 'degree', 'username', 'password', 'unv_dr_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required, including unv_dr_id'}), 400
    if teachers.find_one({'username': data['username']}):
        return jsonify({'error': 'Username already exists'}), 400
    if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
        return jsonify({'error': 'UNV_DR not found'}), 404
    teacher_id = teachers.insert_one(data).inserted_id
    return jsonify({'message': 'Teacher created', 'id': str(teacher_id)}), 201

@app.route('/teacher/<id>', methods=['PUT'])
def update_teacher(id):
    data = request.get_json()
    required_fields = ['name', 'surname', 'degree', 'username', 'password', 'unv_dr_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required, including unv_dr_id'}), 400
    if not unv_drs.find_one({'_id': ObjectId(data['unv_dr_id'])}):
        return jsonify({'error': 'UNV_DR not found'}), 404
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
    log_operation('teacher', 'DELETE', id)
    return jsonify({'message': 'Teacher deleted'}), 200

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
        return jsonify({'message': 'UNV_DR logged in', 'username' : data['username'],  'role': 'unv_dr', 'id': str(user['_id'])}), 200
    
    user = teachers.find_one({'username': data['username'], 'password': data['password']})
    if user:
        return jsonify({'message': 'Teacher logged in', 'role': 'teacher', 'id': str(user['_id'])}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Admin View Operations and Teachers
@app.route('/admin/operations', methods=['GET'])
def view_operations():
    # Fetch all PUT and DELETE operations
    ops = list(operations.find({}, {'_id': 0, 'entity': 1, 'operation': 1, 'user_id': 1, 'timestamp': 1}))
    return jsonify({'operations': ops}), 200

@app.route('/unv_dr', methods=['GET'])
def get_all_unv_drs():
    unv_dr_list = list(unv_drs.find({}, {'_id': 1, 'name': 1, 'surname': 1, 'kafeteria_name': 1, 'username': 1, 'password' : 1}))
    if not unv_dr_list:
        return jsonify({'message': 'No UNV_DRs found', 'unv_drs': []}), 200
    for unv_dr in unv_dr_list:
        unv_dr['_id'] = str(unv_dr['_id'])  # Convert ObjectId to string for JSON
    return jsonify({'unv_drs': unv_dr_list}), 200

@app.route('/admin/unv_dr/<unv_dr_id>/teachers', methods=['GET'])
def view_teachers_by_unv_dr(unv_dr_id):
    try:
        # Verify UNV_DR exists
        if not unv_drs.find_one({'_id': ObjectId(unv_dr_id)}):
            return jsonify({'error': 'UNV_DR not found'}), 404
        
        # Try querying with ObjectId first
        teacher_list = list(teachers.find({'unv_dr_id': ObjectId(unv_dr_id)}, {'_id': 1, 'name': 1, 'surname': 1, 'degree': 1, 'username': 1, 'password': 1}))
        
        # If no results, try querying with string unv_dr_id
        if not teacher_list:
            teacher_list = list(teachers.find({'unv_dr_id': unv_dr_id}, {'_id': 1, 'name': 1, 'surname': 1, 'degree': 1, 'username': 1, 'password': 1}))
        
        
        
        for teacher in teacher_list:
            teacher['_id'] = str(teacher['_id'])
        return jsonify({'teachers': teacher_list}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)