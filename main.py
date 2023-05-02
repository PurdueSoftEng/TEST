from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Mock data for packages
PACKAGES = [
    {"Version": "1.2.3", "Name": "Underscore", "ID": "underscore"},
    {"Version": "1.2.3-2.1.0", "Name": "Lodash", "ID": "lodash"},
    {"Version": "^1.2.3", "Name": "React", "ID": "react1"},
]

@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return f'Howdy {name}!'

@app.route('/authenticate', methods=['PUT'])
def authenticate():
    return jsonify({'message': 'This system does not support authentication.'}), 501

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))