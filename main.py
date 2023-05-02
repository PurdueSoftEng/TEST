
import pymysql
import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table

app = Flask(__name__)

# Mock data for packages
PACKAGES = [
    {"Version": "1.2.3", "Name": "Underscore", "ID": "underscore"},
    {"Version": "1.2.3-2.1.0", "Name": "Lodash", "ID": "lodash"},
    {"Version": "^1.2.3", "Name": "React", "ID": "react1"},
]

# Define table metadata
metadata = MetaData()
test_table = Table('test_table', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(255)),
                   Column('value', Float),
                  )

# Configure database connection settings
db_user = 'root'
db_password = ''
db_name = 'gabby-sql'
cloud_sql_connection_name = 'purdue-soft-eng-384818:us-central1:gabby-sql'
db_socket_dir = '/cloudsql'

# Create PyMySQL connection
conn = pymysql.connect(
    user=db_user,
    password=db_password,
    unix_socket=f'{db_socket_dir}/{cloud_sql_connection_name}',
    db=db_name,
    cursorclass=pymysql.cursors.DictCursor,
)

# Create a test table and insert data
@app.route('/create_table', methods=['POST'])
def create_table():
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE test_table (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))"
    )
    cursor.execute(
        "INSERT INTO test_table (name) VALUES (%s)", 
        ('test_data',)
    )
    conn.commit()
    cursor.close()
    return 'Table created and data inserted successfully.'

@app.route('/add-table', methods=['POST'])
def add_table():
    # Insert new record into the test_table
    query = test_table.insert().values(name='test', value=1.23)
    with conn.cursor() as cursor:
        cursor.execute(str(query))
        conn.commit()

    return jsonify({'message': 'Table added successfully!'})

@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return f'Howdy {name}!'

@app.route('/authenticate', methods=['PUT'])
def authenticate():
    return jsonify({'message': 'This system does not support authentication.'}), 501

# @app.route('/package', methods=['POST'])
# def packages_list():
#     # Parse request body
#     package_queries = request.json

#     for query in package_queries:
#         if 'Name' not in query:
#             return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
#             \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400
    
#     # Check for pagination offset
#     offset = request.args.get('offset', 0)

#     print("offset ", offset)
        
#     # Mock database query
#     results = []

#     for package in PACKAGES:
#         for query in package_queries:
#             print(query)
#             if query == '*' or query == package['Name']:
#                 results.append(package)
    
#     # Apply pagination
#     paginated_results = results[int(offset):int(offset)+10]  # limit to 10 results per page
    
#     # Generate response
#     response = jsonify(paginated_results)
#     response.headers.add('offset', str(int(offset)+10))  # set next page offset in response header
    
#     return response, 200


@app.route('/package', methods=['POST'])
def add_package():
    #Add package to database
    request_body = request.json

    #if (('Content' or 'URL') not in request_body) or ('Content' and 'URL' in request_body):
    if (request_body['URL'] == None) and (request_body['Content'] != None):
        return jsonify({'error': "There is missing field(s) in the PackageData/AuthenticationToken\
        \ or it is formed improperly (e.g. Content and URL are both set), or the\
        \ AuthenticationToken is invalid."}), 400
    

    
    # Check for pagination offset
    #offset = request.args.get('offset', 0)
    response = request_body

    return response, 201

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))