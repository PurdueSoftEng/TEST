import pymysql
import os
import logging
import json
from google.cloud import logging as glogging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from flask import Flask, request, jsonify
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
def reset():
    with conn.cursor() as cursor:
        # Get a list of all the tables in the database
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
    
    tables = tables.json
    logger.info(table[0])
    logger.info(table[0][0])


    if not tables:
        # Return a response indicating that there are no tables to reset
        return jsonify({'message': 'There are no tables to reset.'}), 200

    # For each table, drop it and recreate it with the original schema
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.execute(f"CREATE TABLE {table_name} LIKE {table_name}_backup")

    # Return a response indicating that the tables have been reset
    return jsonify({'message': 'All tables have been reset.'}), 200


# @app.route('/packages', methods=['POST'])
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
    package_name = 'test' # TODO: change this to use the library to get the name
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
    
    id = package_name + version
    content = "base64-encoded package contents" #TODO update this with a content scraping program

    threshold = 0.1
    
    if total_score < threshold:
        return jsonify({'error': "Package is not uploaded due to the disqualified rating."}), 424 

    sql = "SELECT COUNT(*) FROM packages WHERE url=%s AND version=%s"
    val = (url, version)

    with conn.cursor() as cursor:
        cursor.execute(sql, val)
        result = cursor.fetchone()

    logger.info(f"Result: {result}... {url}... {version}")
    logger.info(f"Result: {type(result)}")

    # logger.debug(f"Result: {result[0]}")

    # if result is not None:
    #     # package already exists, return an error response
    #     return jsonify({'error': 'Package exists already.'}), 409

    sql = "INSERT INTO packages (url, version, package_name, jsprogram, content, metric_one, metric_two, metric_three, metric_four, metric_five, metric_six, metric_seven, total_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = [url, version, package_name, jsprogram, content, metric_one, metric_two, metric_three, metric_four, metric_five, metric_six, metric_seven, total_score]

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