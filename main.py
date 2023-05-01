import os
import jsonify

from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return f'Hello {name}!'

@app.route('/authenticate', methods=['PUT'])
def authenticate():
    return jsonify({'message': 'This system does not support authentication.'}), 501



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))