import pymysql
import os
import logging
import json
import re
import metricslib
import base64
import zipfile
import io
from google.cloud import logging as glogging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table
from datetime import datetime, timezone

# data = metricslib.calcscore_py("https://github.com/PurdueSoftEng/TEST")

client = glogging.Client()

handler = CloudLoggingHandler(client)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.info(GITHUB_TOKEN)

app = Flask(__name__)
CORS(app, resources={r"/reset": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/packages": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/package/<id_path>": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/package": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/package/<id_path>/rate": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/package/byName/<name>": {"origins": "https://purduesofteng.github.io/"}})
CORS(app, resources={r"/package/byRegEx": {"origins": "https://purduesofteng.github.io/"}})

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

def package_json_fetch(content):
    try:
        bin = base64.b64decode(content)
    except:
        bin = base64.b64decode(content + '===')
    zf = zipfile.ZipFile(io.BytesIO(bin))
    try:
        obj = zf.getinfo("package.json")
        with zf.open("package.json", 'r') as ptr:
            contents = ptr.read().decode('utf-8')
            return json.loads(contents)
    except:
        return None

# Create a test table and insert data
@app.route('/create_table', methods=['POST'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
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
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def add_table():
    # Insert new record into the test_table
    query = test_table.insert().values(name='test', value=1.23)
    with conn.cursor() as cursor:
        cursor.execute(str(query))
        conn.commit()

    return jsonify({'message': 'Table added successfully!'})

@app.route('/package/byRegEx', methods=['POST'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageByRegExGet():
    logger.info(request.json)
    package_queries = request.json

    if 'RegEx' not in package_queries:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400
    else:
        regex = package_queries["RegEx"]
    
    if regex == "":
        return jsonify({'error': "No packages match the regular expression."}), 404

    try:
        re.compile(regex)
        print("Valid regex!")
    except re.error:
        print("Invalid regex!")

    with conn.cursor() as cursor:
        sql = "SELECT * FROM packages WHERE package_name REGEXP %s"
        val = [regex]
        cursor.execute(sql, val)

        packages = cursor.fetchall()
        if len(packages) == 0:
            return jsonify({'error': "No packages match the regular expression."}), 404
        
    package_metadata_all = []
    for package in packages:
        package_metadata = {
                "Name": package['package_name'],
                "Version": package['version'],
                "ID": package['id']
            }
        package_metadata_all.append(package_metadata)
    
    return jsonify(package_metadata_all), 200

@app.route('/')
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def hello_world():
    logger.debug('Hello, world!')
    name = request.args.get('name', 'World')

    return f'Howdy {name}!'

@app.route('/authenticate', methods=['PUT'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def CreateAuthToken():
    return jsonify({'message': 'This system does not support authentication.'}), 501

@app.route('/reset', methods=['DELETE'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def RegistryReset():
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
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
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

    package_queries = []
    version = ''
    id = ''
    content = ''
    jsprogram = ''
    url = ''
    metadata = ""
    data = ""
    for item in results:
        for field in item.items():
            logger.info(f"Field: {field}")
            if field[0] == 'package_name':
                name = field[1]
            if field[0] == 'version':
                version = field[1]
            if field[0] == 'id':
                id = field[1]
            if field[0] == 'content':
                content = field[1]
            if field[0] == 'jsprogram':
                jsprogram = field[1]
            if field[0] == 'url':
                url = field[1]
        if version:
            metadata = {"Name":packageName, "Version":version, "ID": id}
            data = {"Content":content, "JSProgram":jsprogram, "URL": url }
        package_query = {"metadata": metadata, "data": data}
        
        package_queries.append(package_query)
    
    # Generate response
    total_package_query = jsonify(package_queries)
    total_package_query.headers.add('total_count', str(len(results)))  # set total count in response header
    total_package_query.headers.add('page_count', str(page_num + 1))  # set next page number in response header
    
    # Check for too many results
    max_results = 5
    if len(results) > max_results:
        return jsonify({'error': "Too many packages returned."}), 413
    
    return total_package_query, 200

@app.route('/package/byName/<name>', methods=['DELETE'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageByNameDelete(name):
    #name = request.args.get('name')
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

@app.route('/package/byName/<name>', methods=['GET'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageByNameGet(name):
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
    id = name+version
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
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageCreate():
    logger.info(request.json)
    # Add package to database
    request_body = request.json

    if ('URL' not in request_body) or ((request_body['URL'] == None) and ('Content' not in request_body)) or ((request_body['URL'] != None) and ('Content' in request_body)):
        return jsonify({'error': "There is missing field(s) in the PackageData/AuthenticationToken or it is formed improperly (e.g. Content and URL are both set), or the AuthenticationToken is invalid."}), 400
    
    version = '0.0.0'
    package_name = 'temp'
    jsprogram = ''
    content = ''
    url = ''

    logger.info(f"URL: {url}")

    if ('URL' in request_body):
        url = request_body['URL']
        logger.info(f"URL: {url}")
        version = metricslib.get_version_py(url)
        package_name = metricslib.get_name_py(url)
    
    if ('JSProgram' in request_body):
        jsprogram = request_body['JSProgram']

    if ('Content' in request_body):
        content = request_body['Content']
        data = package_json_fetch(content)
        if data is not None:
            try:
                package_name = data['name']
            except:
                package_name = 'Package'
            try:
                version = data['version']
            except:
                version = '0.0.0'
            try:
                url = data['repository']['url']
            except:
                try:
                    url = data['homepage']
                except:
                    url = ''


    data = metricslib.calcscore_py("https://github.com/PurdueSoftEng/TEST")
    logger.info(f'data: {data}')
    logger.info(f'data: {data[0]}')

    data = json.loads(data)
    logger.info(f'data: {data}')

    metric_one = data['ramp_up']
    metric_two = data['bus_factor']
    metric_three = data['compatibility']
    metric_four = data['correctness']
    metric_five = data['responsiveness']
    metric_six = data['pinning_practice']
    metric_seven = data['reviewed_code']
    total_score = data['net_score']

    package_id = package_name + '-' + version
    content = "base64-encoded package contents" #TODO update this with a content scraping program
    id = package_id

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

@app.route('/package/<id>', methods=['GET'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageRetrieve(id):
    if id is None:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400

    sql = "SELECT COUNT(*) FROM packages WHERE id=%s"
    val = [id]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchone()

    if list(result.values())[0] == 0:
        return jsonify({'error': 'Package does not exist.'}), 404

    sql = "SELECT id, package_name, version, content, url, jsprogram FROM packages WHERE id=%s"
    val = [id]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchall()

    vec = []
    logger.info(f"Result: {result}")
    if result is not None:
        for row in result:
            id_result = result['id']
            package_name = result['package_name']
            version = result['version']
            content = result['content']
            url = result['url']
            jsprogram = result['jsprogram']

            package_data = {
                "metadata": {
                    "Name": package_name,
                    "Version": version,
                    "ID": id_result
                },
                "data": {
                    "Content": content,
                    "URL": url,
                    "JSProgram": jsprogram
                }
            }
            vec.append(package_data)
    return jsonify(vec), 200

@app.route('/package/<id_path>', methods=['PUT'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageUpdate(id_path):
    request_body = request.json

    logger.info(f"Request_body: {request_body}")
    logger.info(f"Request_body['metadata']: {request_body['metadata']}")
    logger.info(f"Request_body['data']: {request_body['data']}")

    meta = request_body['metadata']
    dat = request_body['data']

    if ('Name' not in meta) or ('ID' not in meta) or ('Version' not in meta):
        return jsonify({'error': "There is missing field(s) in the PackageData/AuthenticationToken or it is formed improperly (e.g. Content and URL are both set), or the AuthenticationToken is invalid."}), 400
    
    id = meta['ID']
    version = meta['Version']
    package_name = meta['Name']

    sql = "SELECT COUNT(*) FROM packages WHERE id=%s"
    val = [id_path]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchone()

    if list(result.values())[0] == 0:
        return jsonify({'error': 'Package does not exist.'}), 404

    sql = "UPDATE packages SET package_id=%s, package_name=%s, version=%s WHERE id=%s"
    val = [id, package_name, version, id_path]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        conn.commit()

    return jsonify({'message': "Version is updated."}), 200


@app.route('/package/<id>', methods=['DELETE'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageDelete(id):   
    if id is None:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400

    with conn.cursor() as cursor:
        sql = "SELECT * FROM packages WHERE id=%s"
        val = [id]
        cursor.execute(sql, val)

        packages = cursor.fetchall()
        if len(packages) == 0:
            return jsonify({'error': "Package does not exist."}), 404
        else:
            sql = "DELETE FROM packages WHERE id=%s"
            cursor.execute(sql, val)
            conn.commit()

    return jsonify({'message': "Package is deleted."}), 200

@app.route('/package/<id>/rate', methods=['GET'])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def PackageRate(id):
    if id is None:
        return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
        \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400

    sql = "SELECT * FROM packages WHERE id=%s"
    val = [id]
    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        packages = cursor.fetchall()
        if len(packages) == 0:
            return jsonify({'error': "Package does not exist."}), 404

    sql = "SELECT metric_one, metric_two, metric_three, metric_four, metric_five, metric_six, metric_seven, total_score FROM packages WHERE id=%s"
    val = [id]

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchall()
        logger.info(f"Result: {result}")
    

    if result is None:
        return jsonify({'error': 'Package does not exist.'}), 404

    result = result[0]

    ramp_up = result['metric_one']
    bus_factor = result['metric_two']
    license = result['metric_three']
    correctness = result['metric_four']
    resp_maintain = result['metric_five']
    pinning = result['metric_six']
    pull_request = result['metric_seven']
    net_score = result['total_score']

    package_rating = {
        "BusFactor": bus_factor,
        "Correctness": correctness, 
        "RampUp": ramp_up, 
        "ResponsiveMaintainer": resp_maintain, 
        "LicenseScore": license, 
        "GoodPinningPractice": pinning,
        "PullRequest": pull_request,
        "NetScore": net_score
    }

    json_data = json.dumps(package_rating)
    return json_data, 200    

if __name__ == "__main__":

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))