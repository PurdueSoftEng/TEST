import os
from flask import Flask, request, jsonify
import mysql.connector
import requests

app = Flask(__name__)

# Mock data for packages
PACKAGES = [
    {"Version": "1.2.3", "Name": "Underscore", "ID": "underscore"},
    {"Version": "1.2.3-2.1.0", "Name": "Lodash", "ID": "lodash"},
    {"Version": "^1.2.3", "Name": "React", "ID": "react1"},
]

# # Get database connection parameters from environment variables
# db_host = os.environ.get('DB_HOST')
# db_user = os.environ.get('DB_USER')
# db_password = os.environ.get('DB_PASSWORD')
# db_name = os.environ.get('DB_NAME')

# # Configure database connection
# db = mysql.connector.connect(
#     host=db_host,
#     user=db_user,
#     password=db_password,
#     database=db_name
# )

# Get database connection parameters from environment variables
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

# Get Cloud SQL instance hostname from the metadata server
metadata_server_url = 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/'
instance_hostname = requests.get(metadata_server_url + 'hostname', headers={'Metadata-Flavor': 'Google'}).text

# Construct database connection parameters
db_config = {
    'user': db_user,
    'password': db_password,
    'host': instance_hostname,
    'database': db_name,
    'unix_socket': '/cloudsql/{}'.format(instance_hostname)
}

# Establish database connection
db = mysql.connector.connect(**db_config)

@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return f'Howdy {name}!'

@app.route('/checkdbcredentials')
def check_db_credentials():
    return f'Dbhost: {db_host}\nDbuser: {db_user}\nDbpassword: {db_password}\nDbdb: {db_name}!'

@app.route('/authenticate', methods=['PUT'])
def authenticate():
    return jsonify({'message': 'This system does not support authentication.'}), 501

@app.route('/packages', methods=['POST'])
def packages_list():
    # Parse request body
    package_queries = request.json

    for query in package_queries:
        if 'Name' not in query:
            return jsonify({'error': "There is missing field(s) in the PackageQuery/AuthenticationToken\
            \ or it is formed improperly, or the AuthenticationToken is invalid."}), 400
    
    # Check for pagination offset
    offset = request.args.get('offset', 0)

    print("offset ", offset)
        
    # Mock database query
    results = []

    for package in PACKAGES:
        for query in package_queries:
            print(query)
            if query == '*' or query == package['Name']:
                results.append(package)
    
    # Apply pagination
    paginated_results = results[int(offset):int(offset)+10]  # limit to 10 results per page
    
    # Generate response
    response = jsonify(paginated_results)
    response.headers.add('offset', str(int(offset)+10))  # set next page offset in response header
    
    return response, 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))