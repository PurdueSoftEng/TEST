import re
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Endpoint for getting packages
@app.route('/packages', methods=['POST'])
def get_packages():
    # Get the request body as JSON
    request_body = request.get_json()
    if request_body is None:
        return jsonify(error="Request body must be a JSON object"), 400

    # Get the offset parameter from the query string
    offset = request.args.get('offset', default=0, type=int)

    # Check if the request is for enumerating all packages
    if len(request_body) == 1 and request_body[0].get('Name') == '*':
        result = packages[offset:]
    else:
        # Filter the packages by the query
        result = []
        for package in packages:
            for query in request_body:
                if query.get('Name') == package.get('Name') and query.get('Version') == package.get('Version'):
                    result.append(package)

    # Paginate the results
    max_results = 100
    if len(result) > max_results:
        return jsonify(error=f"Too many packages returned (maximum is {max_results})"), 413
    else:
        result_page = result[offset:offset+max_results]

        # Prepare the response
        response = jsonify(result_page)

        # Set the response header with the next offset
        next_offset = offset + len(result_page)
        response.headers['offset'] = str(next_offset)

        return response, 200
    
# Endpoint to reset the registry
@app.route('/reset', methods=['DELETE'])
@authenticate
def reset_registry():
    # Add code to reset the registry here
    return jsonify({'message': 'Registry is reset.'}), 200

# Error handler for missing or invalid authentication token
@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({'error': 'Missing or invalid authentication token.'}), 400

# Error handler for unauthorized access
@app.errorhandler(401)
def handle_unauthorized_access(e):
    return jsonify({'error': 'Unauthorized access.'}), 401

@app.route('/package/byRegEx', methods=['POST'])
def package_by_regex():
    # Extract the request body JSON data
    request_data = request.json

    # Validate the request body
    if 'RegEx' not in request_data:
        return jsonify({'message': 'Missing RegEx field in request body'}), 400

    # Extract the regular expression pattern from the request body
    regex_pattern = request_data['RegEx']

    # Perform the package search based on the regular expression pattern
    # Here, we simply return a hard-coded list of package metadata
    package_metadata = [
        {'Name': 'Underscore', 'Version': '1.2.3'},
        {'Name': 'Lodash', 'Version': '1.2.3-2.1.0'},
        {'Name': 'React', 'Version': '^1.2.3'}
    ]
    matching_package_metadata = []
    for metadata in package_metadata:
        if re.search(regex_pattern, metadata['Name']) or re.search(regex_pattern, metadata['Version']):
            matching_package_metadata.append(metadata)

    # Return the matching package metadata as a JSON response
    if len(matching_package_metadata) > 0:
        return jsonify(matching_package_metadata), 200
    else:
        return jsonify({'message': 'No package found under this regex'}), 404

    from flask import Flask, jsonify, request


@app.route('/package/<string:id>/rate', methods=['GET'])
def get_package_rating(id):
    # get the package rating using the provided ID
    # replace the return statement with the actual code for retrieving the rating
    rating = {'RampUp': 0.8, 'Correctness': 0.9, 'BusFactor': 0.7,
              'ResponsiveMaintainer': 0.6, 'LicenseScore': 0.85,
              'GoodPinningPractice': 0.5, 'PullRequest': 0.75, 'NetScore': 0.77}

    # check if all required metrics are present in the request
    required_metrics = ['RampUp', 'Correctness', 'BusFactor', 'ResponsiveMaintainer',
                        'LicenseScore', 'GoodPinningPractice', 'PullRequest', 'NetScore']
    missing_metrics = [metric for metric in required_metrics if metric not in request.args]
    if missing_metrics:
        return jsonify({'error': f'Missing metrics: {", ".join(missing_metrics)}'}), 400

    # construct the package rating object from the request arguments
    package_rating = {}
    for metric in required_metrics:
        value = float(request.args.get(metric, -1))
        if value < 0:
            return jsonify({'error': f'Missing or invalid value for metric {metric}'}), 400
        package_rating[metric] = value

    # return the package rating object as JSON
    return jsonify(package_rating), 200


if __name__ == '__main__':
    app.run(debug=True)