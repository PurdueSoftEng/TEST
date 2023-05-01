from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

# Mock data for packages
PACKAGES = [
    {"Version": "1.2.3", "Name": "Underscore", "ID": "underscore"},
    {"Version": "1.2.3-2.1.0", "Name": "Lodash", "ID": "lodash"},
    {"Version": "^1.2.3", "Name": "React", "ID": "react"},
]

# Define a dictionary of authorized users and their passwords
authorized_users = {
    "alice": "password123",
    "bob": "password456"
}

# Define an endpoint to handle authentication requests
@app.route('/authenticate', methods=['POST'])
def authenticate():
    # Parse the authentication request body
    req_data = request.get_json()
    username = req_data['User']['name']
    password = req_data['Secret']['password']

    # Check if the provided credentials are valid
    if username in authorized_users and authorized_users[username] == password:
        # Return a JWT token as the authentication token
        auth_token = generate_jwt_token(username)
        return jsonify(auth_token), 200
    else:
        return "Invalid username or password", 401

# Define a function to generate a JWT token for the authenticated user
def generate_jwt_token(username):
    # Use a library like PyJWT to generate a JWT token
    jwt_secret = 'my_secret_key'
    token = jwt.encode({'username': username}, jwt_secret, algorithm='HS256')
    return token

@app.route('/packages', methods=['POST'])
def packages_list():
    # Parse request body
    package_queries = request.json
    
    # Check for authentication token
    auth_token = request.headers.get('X-Authorization')
    if not auth_token:
        return jsonify({"error": "Authentication token missing"}), 400
    
    # Check for pagination offset
    offset = request.args.get('offset', 0)
    
    # Mock database query
    results = []
    for package in PACKAGES:
        for query in package_queries:
            if query['Name'] == '*' or query == package:
                results.append(package)
    
    # Apply pagination
    paginated_results = results[int(offset):int(offset)+10]  # limit to 10 results per page
    
    # Generate response
    response = jsonify(paginated_results)
    response.headers.add('offset', str(int(offset)+10))  # set next page offset in response header
    
    return response, 200

if __name__ == '__main__':
    app.run()