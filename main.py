
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

# # Set up database connection details
# db_user = os.environ.get('DB_USER')
# db_password = os.environ.get('DB_PASSWORD')
# db_name = os.environ.get('DB_NAME')
# db_host = os.environ.get('DB_HOST')
# db_port = os.environ.get('DB_PORT')

# # Create PyMySQL connection
# conn = pymysql.connect(
#     user=db_user,
#     password=db_password,
#     host=db_host,
#     port=int(db_port),
#     database=db_name,
# )

# # Create SQLAlchemy engine
# engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}', echo=True)

# Define table metadata
metadata = MetaData()
test_table = Table('test_table', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(255)),
                   Column('value', Float),
                  )

# # Create the table in the database
# metadata.create_all(engine)

# @app.route('/add-table', methods=['POST'])
# def add_table():
#     # Insert new record into the test_table
#     query = test_table.insert().values(name='test', value=1.23)
#     with conn.cursor() as cursor:
#         cursor.execute(str(query))
#         conn.commit()

#     return jsonify({'message': 'Table added successfully!'})

@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return f'Howdy {name}!'

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