import pymysql
import os
import logging
import json
from google.cloud import logging as glogging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table

client = glogging.Client()

handler = CloudLoggingHandler(client)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

app = Flask(__name__)
CORS(app, resources={r"/reset": {"origins": "https://purduesofteng.github.io/"}})

# Configure database connection settings
db_user = 'root'
db_password = ''
db_name = 'gabby-sql'
cloud_sql_connection_name = 'purdue-soft-eng-384818:us-central1:gabby-sql'
db_socket_dir = '/cloudsql'
db_port = 3306

# Create PyMySQL connection
conn = pymysql.connect(
    user=db_user,
    password=db_password,
    unix_socket=f'{db_socket_dir}/{cloud_sql_connection_name}',
    #port=db_port,
    db=db_name,
    cursorclass=pymysql.cursors.DictCursor,
)

# Define table metadata
metadata = MetaData()
test_table = Table('test_table', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(255)),
                   Column('value', Float),
                  )

packages_table = Table('packages', metadata,
                       Column('package_id', Integer, primary_key=True),
                       Column('url', String),
                       Column('version', String),
                       Column('package_name', String),
                       Column('jsprogram', String),
                       Column('content', String),
                       Column('metric_one', Float),
                       Column('metric_two', Float),
                       Column('metric_three', Float),
                       Column('metric_four', Float),
                       Column('metric_five', Float),
                       Column('metric_six', Float),
                       Column('metric_seven', Float),
                       Column('total_score', Float),
                       Column('id', String),
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
    logger.debug('Hello, world!')
    name = request.args.get('name', 'World')
    return f'Howdy {name}!'

@app.route('/authenticate', methods=['PUT'])
def CreateAuthToken():
    return jsonify({'message': 'This system does not support authentication.'}), 501

@app.route('/reset', methods=['DELETE'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def reset():
    with conn.cursor() as cursor:
            # Get a list of all the tables in the database
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        logger.info(f"Tables: {tables}")

        if not tables:
            # Return a response indicating that there are no tables to reset
            return jsonify({'message': 'There are no tables to reset.'}), 200

        # For each table, drop it and recreate it with the original schema
        for table in tables:
            table_name = list(table.values())[0]
            if not table_name.endswith('_backup'):
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"CREATE TABLE {table_name} LIKE {table_name}_backup")

    # Return a response indicating that the tables have been reset
    return jsonify({'message': 'All tables have been reset.'}), 200

@app.route('/packages', methods=['POST'])
def PackagesList():
    # Parse request body
    package_queries = request.json

    if 'Version' in package_queries:
        version = package_queries['Version']
    else:
        version = None

    if 'Name' not in package_queries:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400
    
    packageName = package_queries['Name']
    
    # Check for pagination offset and limit
    max_page_size = 100
    page_size = min(int(request.args.get('page_size', 10)), max_page_size)
    page_num = int(request.args.get('page', 0))
    offset = page_num * page_size
        
    with conn.cursor() as cursor:
        if packageName != '*':
            sql = "SELECT * FROM packages WHERE package_name=%s"
            val = [packageName]
            if version is not None:
                sql += " AND version=%s"
                val.append(version)
            sql += " LIMIT %s OFFSET %s"
            val.extend([page_size, offset])
            cursor.execute(sql, val)
        else:
            sql = "SELECT * FROM packages LIMIT %s OFFSET %s"
            val = [page_size, offset]
            cursor.execute(sql, val)

        results = cursor.fetchall()

    logger.info(f"Results: {results}")
    packages = []

    for item in results:
        for field in item.items():
            logger.info('field[0]: %s', field[0])
            if field[0] == 'name':
                name = {
                        "name": field[1]
                    }
            if field[0] == 'version':
                version = field[1]

        if version:
            package_query = {
                "Name": name,
                "Version": version
            }
        else:
            package_query = {
                "Name": name,
            }
    
    # Generate response
    packageMetadata = jsonify(results)
    package_query.headers.add('total_count', str(len(results)))  # set total count in response header
    package_query.headers.add('page_count', str(page_num + 1))  # set next page number in response header
    
    # Check for too many results
    max_results = 1000
    if len(results) > max_results:
        return jsonify({'error': "Too many packages returned."}), 413
    
    return package_query, 200

@app.route('/package/byName', methods=['DELETE'])
def PackageByNameDelete():
    name = request.args.get('name')
    if name is None:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400

    with conn.cursor() as cursor:
        sql = "SELECT * FROM packages WHERE package_name=%s"
        val = [name]
        cursor.execute(sql, val)

        packages = cursor.fetchall()
        if len(packages) == 0:
            return jsonify({'error': "Package does not exist."}), 404
        else:
            sql = "DELETE FROM packages WHERE package_name=%s"
            cursor.execute(sql, val)
            conn.commit()

    return jsonify({'message': "Package is deleted."}), 200

@app.route('/package/byName', methods=['GET'])
def PackageByNameGet():
    name = request.args.get('name')
    if name is None:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400
    
    with conn.cursor() as cursor:
        sql = "SELECT * FROM packages WHERE package_name=%s"
        val = [name]
        cursor.execute(sql, val)

        packages = cursor.fetchall()
        if len(packages) == 0:
            return jsonify({'error': "No such package."}), 404

    version = "1.2.3"
    content = "tempcontentstring"
    jsprogram = "testprogram"
    url = ""
    package_history = {
        "PackageMetadata": {
            "Name": name,
            "Version": version,
            "ID": id
        },
        "PackageData": {
            "Content": content,
            "URL": url,
            "JSProgram": jsprogram
        }
    }

    json_data = json.dumps(package_history)
    return package_history, 200

@app.route('/package', methods=['POST'])
def PackageCreate():
    # Add package to database
    request_body = request.json

    if ('URL' not in request_body) or ((request_body['URL'] == None) and ('Content' not in request_body)) or ((request_body['URL'] != None) and ('Content' in request_body)):
        return jsonify({'error': "There is missing field(s) in the PackageData/AuthenticationToken or it is formed improperly (e.g. Content and URL are both set), or the AuthenticationToken is invalid."}), 400
    
    if ('URL' in request_body):
        url = request_body['URL']
    else:
        url = ''
    
    url = request_body['URL']
    version = "1.0.0" # TODO: change this to use the library to get the version
    package_name = 'temp' # TODO: change this to use the library to get the name
    if ('JSProgram' in request_body):
        jsprogram = request_body['JSProgram']
    else:
        jsprogram = ''

    if ('Content' in request_body):
        content = request_body['Content']
    else:
        content = ''

    metric_one = 0
    metric_two = 0
    metric_three = 0
    metric_four = 0
    metric_five = 0
    metric_six = 0
    metric_seven = 0.6
    total_score = 0.6
    
    pakcage_id = package_name + version
    content = "base64-encoded package contents" #TODO update this with a content scraping program
    id = "id"  #TODO update this metrics

    threshold = 0.1
    
    if total_score < threshold:
        return jsonify({'error': "Package is not uploaded due to the disqualified rating."}), 424 

    sql = "SELECT COUNT(*) FROM packages WHERE url=%s AND version=%s"
    val = (url, version)

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchone()

    if list(result.values())[0] > 0:
        # package already exists, return an error response
        return jsonify({'error': 'Package exists already.'}), 409

    sql = "INSERT INTO packages (url, version, package_name, jsprogram, content, metric_one, metric_two, metric_three, metric_four, metric_five, metric_six, metric_seven, total_score, id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = [url, version, package_name, jsprogram, content, metric_one, metric_two, metric_three, metric_four, metric_five, metric_six, metric_seven, total_score, id]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        conn.commit()

    package_data = {
        "metadata": {
            "Name": package_name,
            "Version": version,
            "ID": id
        },
        "data": {
            "Content": content,
            "URL": url,
            "JSProgram": jsprogram
        }
    }

    json_data = json.dumps(package_data)

    return json_data, 201

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))