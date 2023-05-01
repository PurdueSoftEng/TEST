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