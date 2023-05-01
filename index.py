from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

# Mock data for packages
PACKAGES = [
    {"Version": "1.2.3", "Name": "Underscore", "ID": "underscore"},
    {"Version": "1.2.3-2.1.0", "Name": "Lodash", "ID": "lodash"},
    {"Version": "^1.2.3", "Name": "React", "ID": "react1"},
]

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

if __name__ == '__main__':
    app.run()