"""
HTTP Server Shell
Author: Ori Kelty

A basic  HTTP server I implemented from scratch using Python sockets.
It supports standard GET requests, serves static files from a 'webroot' directory,
and handles common HTTP responses (200, 404, 500, and more).
"""
import socket
import os
import logging

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
DEFAULT_URL = '/index.html'
WEBROOT = 'webroot'
UPLOAD_IMAGE = 'upload/'


REDIRECTION_DICTIONARY = {
    '/moved': '/'
}

CONTENT_TYPES = {
    'html': 'text/html; charset=utf-8',
    'jpg': 'image/jpeg',
    'css': 'text/css',
    'js': 'text/javascript; charset=UTF-8',
    'txt': 'text/plain',
    'ico': 'image/x-icon',
    'gif': 'image/jpeg',
    'png': 'image/png'
}


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: the file data
    """
    logger.debug("Reading file: " + str(file_name))
    try:
        file_extension = file_name.split('.')[-1]
        if file_extension in ['jpg', 'ico', 'gif', 'png']:
            logger.debug("Opening " + str(file_name) + " in binary mode")
            with open(file_name, 'rb') as f:
                data = f.read()
                logger.info("Successfully read binary file " + str(file_name) + " (" + str(len(data)) + " bytes)")
                return data
        else:
            logger.debug("Opening " + str(file_name) + " in text mode")
            with open(file_name, 'r') as f:
                content = f.read()
                data = content.encode()
                logger.info("Successfully read text file " + str(file_name) + " (" + str(len(data)) + " bytes)")
                return data
    except FileNotFoundError:
        logger.error("File not found: " + str(file_name))
        return None
    except Exception as e:
        logger.error("Error reading file " + str(file_name) + ": " + str(e))
        return None


def build_http_response(status_code, status_text, headers, body=b''):
    """
    Build a complete HTTP response
    :param status_code: HTTP status code
    :param status_text: Status text
    :param headers: Dictionary of headers
    :param body: Response body as bytes
    :return: Complete HTTP response as bytes
    """
    logger.debug("Building HTTP response: " + str(status_code) + " " + str(status_text))
    response_line = "HTTP/1.1 " + str(status_code) + " " + str(status_text) + "\r\n"
    header_lines = ""

    for key, value in headers.items():
        header_lines += key + ": " + value + "\r\n"
        logger.debug("  Header: " + key + ": " + value)

    header_lines += "\r\n"
    http_response = response_line.encode() + header_lines.encode() + body
    logger.info("HTTP Response built: " + str(status_code) + " " + str(status_text) + ", Total size: " + str(len(http_response)) + " bytes")
    print("Response headers:")
    print(response_line + header_lines)

    return http_response


def handle_client_request(resource, client_socket, image_len):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param image_len:
    :param resource
    :param client_socket
    :return: None
    """
    logger.info("Handling request for resource: " + str(resource))
    if resource == '/' or resource == '':
        logger.debug("Resource is default, redirecting to: " + DEFAULT_URL)
        resource = DEFAULT_URL

    if resource == '/forbidden':
        logger.warning("Forbidden resource requested: /forbidden")
        print("Handling special URI: /forbidden")
        headers = {'Content-Length': '0'}
        http_response = build_http_response(403, 'FORBIDDEN', headers)
        client_socket.send(http_response)
        logger.info("Sent 403 FORBIDDEN response")
        print("Sent 403 FORBIDDEN response")
        return

    if resource == '/error':
        logger.warning("Error resource requested: /error")
        print("Handling special URI: /error")
        headers = {'Content-Length': '0'}
        http_response = build_http_response(500, 'INTERNAL SERVER ERROR', headers)
        client_socket.send(http_response)
        logger.info("Sent 500 INTERNAL SERVER ERROR response")
        print("Sent 500 INTERNAL SERVER ERROR response")
        return

    if resource in REDIRECTION_DICTIONARY:
        new_location = REDIRECTION_DICTIONARY[resource]
        logger.info("Redirecting " + str(resource) + " to " + str(new_location))
        print("Redirecting " + str(resource) + " to " + str(new_location))
        headers = {
            'Location': new_location,
            'Content-Length': '0'
        }
        http_response = build_http_response(302, 'MOVED TEMPORARILY', headers)
        client_socket.send(http_response)
        logger.info("Sent 302 MOVED TEMPORARILY response to " + str(new_location))
        print("Sent 302 MOVED TEMPORARILY response")
        return

    if resource.startswith('/'):
        resource = resource[1:]

    try:
        method , variables = resource.split("?")
        logger.debug("Parsed method: " + str(method) + ", variables: " + str(variables))
        if method == "calculate-next":
            logger.info("Handling calculate-next request")
            num = variables.split("=")[1]
            logger.debug("Extracted number parameter: " + str(num))

            try:
                num = float(num)
                logger.debug("Successfully parsed number: " + str(num))
                next_num = float(num) + 1
                logger.debug("Calculated next number: " + str(next_num))
                num_len = len(str(next_num))
                headers = {
                    'Content-Type': 'text/plain',
                    'Content-Length': str(num_len)

                }
                http_response = build_http_response(200, 'OK', headers)
                client_socket.send(http_response)
                client_socket.send(str(next_num).encode())
                logger.info("Sent calculate-next response: " + str(next_num))
                return

            except Exception as e:
                print("Error: An String Was Submitted , " + str(e))
                logger.error("Failed to parse number in calculate-next: " + str(e))
                headers = {
                    'Content-Type': 'text/plain',
                    'Content-Length': "0"

                }
                http_response = build_http_response(400, 'Bad Request', headers)
                client_socket.send(http_response)
                logger.info("Sent 400 Bad Request response for calculate-next")
                return


        if method == "calculate-area":
            logger.info("Handling calculate-area request")
            height , width = variables.split("&")[0].split("=") , variables.split("&")[1].split("=")
            logger.debug("Parsed height variable: " + str(height) + ", width variable: " + str(width))
            try:
                height = float(height[1])
                width = float(width[1])
                logger.debug("Successfully parsed height: " + str(height) + ", width: " + str(width))

                area = ((height*width)/2)
                logger.debug("Calculated area: " + str(area))
                area_len = len(str(area))
                headers = {
                    'Content-Type': 'text/plain',
                    'Content-Length': str(area_len)
                }
                http_response = build_http_response(200, 'OK', headers)
                client_socket.send(http_response)
                client_socket.send(str(area).encode())
                logger.info("Sent calculate-area response: " + str(area))
                return
            except Exception as e:
                print("Error : An String Was Submitted , " + str(e))
                logger.error("Failed to parse height/width in calculate-area: " + str(e))
                headers = {
                    'Content-Type': 'text/plain',
                    'Content-Length': "0"
                }
                http_response = build_http_response(400, 'Bad Request', headers)
                client_socket.send(http_response)
                logger.info("Sent 400 Bad Request response for calculate-area")
                return

        if method == 'upload':
            logger.info("Handling upload request")
            file_name = variables.split("=")[1]
            logger.debug("Upload file name: " + str(file_name))
            logger.debug("Expecting " + str(image_len) + " bytes of image data")
            data_to_receive = 0
            photo_data = b''
            while data_to_receive < int(image_len):
                photo_data += client_socket.recv(1)
                data_to_receive+=1
            logger.debug("Received " + str(len(photo_data)) + " bytes of image data")
            with open(UPLOAD_IMAGE+file_name, 'wb') as f:
                f.write(photo_data)
            logger.info("Successfully saved uploaded file: " + str(UPLOAD_IMAGE+file_name))
            headers = {
                'Content-Type': "text/plain",
                'Content-Length': '0'
            }
            http_response = build_http_response(200, 'OK', headers)
            client_socket.send(http_response)
            logger.info("Sent 200 OK response for upload")
            return
        if method == 'image':
            logger.info("Handling image request")
            file_name = variables.split("=")[1]
            logger.debug("Image file name: " + str(file_name))
            image_path = UPLOAD_IMAGE + file_name
            logger.debug("Reading image from: " + str(image_path))
            with open(image_path , 'rb') as f:
               photo_data = f.read()
            logger.debug("Read " + str(len(photo_data)) + " bytes from image file")
            photo_len = str(len(photo_data))
            headers = {
                'Content-Type': "text/plain",
                'Content-Length': photo_len
            }
            http_response = build_http_response(200, 'OK', headers)
            client_socket.send(http_response)
            client_socket.send(photo_data)
            logger.info("Sent image response: " + str(file_name) + " (" + str(photo_len) + " bytes)")
            return



    except Exception as e:
        print("Error " + str(e))
        logger.error("Error parsing resource with query parameters: " + str(e))




    file_path = os.path.join(WEBROOT, resource)
    logger.debug("Resolved file path: " + str(file_path))

    if not os.path.isfile(file_path):
        logger.warning("File not found: " + str(file_path))
        print("File not found: " + str(file_path))
        headers = {'Content-Length': '0'}
        http_response = build_http_response(404, 'NOT FOUND', headers)
        client_socket.send(http_response)
        logger.info("Sent 404 NOT FOUND response")
        print("Sent 404 NOT FOUND response")
        return

    file_extension = resource.split('.')[-1] if '.' in resource else 'html'
    logger.debug("File extension: " + str(file_extension))

    content_type = CONTENT_TYPES.get(file_extension, 'application/octet-stream')
    logger.debug("Content-Type: " + str(content_type))

    data = get_file_data(file_path)

    if data is None:
        logger.error("Failed to read file: " + str(file_path))
        print("Error: Failed to read file: " + str(file_path))
        headers = {'Content-Length': '0'}
        http_response = build_http_response(500, 'INTERNAL SERVER ERROR', headers)
        client_socket.send(http_response)
        logger.info("Sent 500 INTERNAL SERVER ERROR response")
        print("Sent 500 INTERNAL SERVER ERROR response")
        return

    headers = {
        'Content-Type': content_type,
        'Content-Length': str(len(data))
    }

    http_response = build_http_response(200, 'OK', headers, data)
    client_socket.send(http_response)
    logger.info("Sent 200 OK response for " + str(resource) + " (" + str(len(data)) + " bytes)")
    print("Sending response: 200 OK, Content-Type: " + str(content_type) + ", Content-Length: " + str(len(data)))


def validate_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource)
    """
    logger.debug("Validating HTTP request")
    try:
        lines = request.split('\r\n')
        if not lines:
            logger.warning("Empty request received")
            return False, ''

        request_line = lines[0]
        logger.debug("Request line: " + str(request_line))
        parts = request_line.split(' ')

        if len(parts) != 3:
            logger.warning("Invalid request format - expected 3 parts, got " + str(len(parts)))
            return False, ''

        method, uri, http_version = parts

        if method != 'GET' and method != 'POST':
            logger.warning("Invalid HTTP method: " + str(method) + " (expected GET)")
            return False, '' , None


        if not http_version.startswith('HTTP/1.1'):
            logger.warning("Invalid HTTP version: " + str(http_version))
            return False, '' , None
        if method == 'GET':
            logger.info("Valid HTTP request: GET" + str(uri))
            return True, uri , None
        if method == 'POST':
            logger.info("Valid HTTP request: POST" + str(uri))
            content_length = lines[3].split(":")[1]
            return True , uri , content_length

    except Exception as e:
        logger.error("Error validating request: " + str(e))
        return False, ''


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    print('Client connected')
    logger.info('Client connected')
    try:
        while True:
            logger.debug("Waiting for client request...")
            client_request = client_socket.recv(1024).decode()

            if not client_request:
                logger.debug("Empty request received, closing connection")
                break

            print("Received request:\n" + str(client_request[:200]) + "...")
            logger.debug("Received " + str(len(client_request)) + " bytes")
            logger.debug("Request preview: " + str(client_request[:200]))

            valid_http, resource , image_len2 = validate_http_request(client_request)

            if valid_http:
                print('Got a valid HTTP request for: ' + str(resource))
                logger.info('Processing valid HTTP request for: ' + str(resource))
                handle_client_request(resource, client_socket, image_len2)
                break
            else:
                print('Error: Not a valid HTTP request')
                logger.error('Invalid HTTP request received')
                headers = {'Content-Length': '0'}
                http_response = build_http_response(400, 'BAD REQUEST', headers)
                client_socket.send(http_response)
                logger.info("Sent 400 BAD REQUEST response")
                print("Sent 400 BAD REQUEST response")
                break

    except socket.timeout:
        print('Socket timeout - closing connection')
        logger.warning('Socket timeout - closing connection')
    except Exception as e:
        print('Error handling client: ' + str(e))
        logger.error('Error handling client: ' + str(e))

    print('Closing connection')
    logger.info('Closing connection')


def main():
    """Main server loop"""
    logger.info("Starting HTTP Server")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logger.debug("Server socket created")

    try:
        server_socket.bind((IP, PORT))
        logger.info("Socket bound to " + str(IP) + ":" + str(PORT))

        server_socket.listen(QUEUE_SIZE)
        logger.info("Server listening with queue size: " + str(QUEUE_SIZE))
        logger.info("Webroot directory: " + str(os.path.abspath(WEBROOT)))
        print("Listening for connections on port " + str(PORT))
        print("Webroot directory: " + os.path.abspath(WEBROOT))

        while True:
            logger.debug("Waiting for new connection...")
            client_socket, client_address = server_socket.accept()
            print('New connection received from ' + str(client_address))
            logger.info('New connection received from ' + str(client_address))

            try:
                client_socket.settimeout(SOCKET_TIMEOUT)
                logger.debug("Socket timeout set to " + str(SOCKET_TIMEOUT) + " seconds")
                handle_client(client_socket)
            except socket.error as err:
                print('received socket exception - ' + str(err))
                logger.error('Socket exception: ' + str(err))
            finally:
                client_socket.close()
                logger.debug("Connection closed for " + str(client_address))

    except socket.error as err:
        print('received socket exception - ' + str(err))
        logger.critical('Fatal socket exception: ' + str(err))
    finally:
        server_socket.close()
        logger.info("Server socket closed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename="server.log",
        filemode="w",
    )
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("HTTP Server - Starting Validation")
    print("=" * 60)
    logger.info("=" * 60)
    logger.info("HTTP Server - Starting Validation")
    logger.info("=" * 60)

    print("Checking WEBROOT directory: " + str(WEBROOT))
    logger.info("Checking WEBROOT directory: " + str(WEBROOT))
    assert os.path.exists(WEBROOT), "ERROR: WEBROOT directory '" + str(WEBROOT) + "' does not exist!"
    assert os.path.isdir(WEBROOT), "ERROR: WEBROOT '" + str(WEBROOT) + "' is not a directory!"
    print("WEBROOT directory exists: " + str(os.path.abspath(WEBROOT)))
    logger.info("WEBROOT directory exists: " + str(os.path.abspath(WEBROOT)))

    index_path = os.path.join(WEBROOT, 'index.html')
    print("Checking for index.html: " + str(index_path))
    logger.info("Checking for index.html: " + str(index_path))
    assert os.path.isfile(index_path), "ERROR: index.html not found in WEBROOT at '" + str(index_path) + "'"
    print("index.html found")
    logger.info("index.html found")

    print("Validating PORT: " + str(PORT))
    logger.info("Validating PORT: " + str(PORT))
    assert isinstance(PORT, int), "ERROR: PORT must be an integer"
    assert 1 <= PORT <= 65535, "ERROR: PORT must be between 1 and 65535, got " + str(PORT)
    print("PORT is valid: " + str(PORT))
    logger.info("PORT is valid: " + str(PORT))

    print("Validating IP: " + str(IP))
    logger.info("Validating IP: " + str(IP))
    assert isinstance(IP, str), "ERROR: IP must be a string"
    assert IP in ['0.0.0.0', '127.0.0.1', 'localhost'] or '.' in IP, "ERROR: Invalid IP format: " + str(IP)
    print("IP is valid: " + str(IP))
    logger.info("IP is valid: " + str(IP))

    print("Validating QUEUE_SIZE: " + str(QUEUE_SIZE))
    logger.info("Validating QUEUE_SIZE: " + str(QUEUE_SIZE))
    assert isinstance(QUEUE_SIZE, int), "ERROR: QUEUE_SIZE must be an integer"
    assert QUEUE_SIZE > 0, "ERROR: QUEUE_SIZE must be positive, got " + str(QUEUE_SIZE)
    print("QUEUE_SIZE is valid: " + str(QUEUE_SIZE))
    logger.info("QUEUE_SIZE is valid: " + str(QUEUE_SIZE))

    print("Validating SOCKET_TIMEOUT: " + str(SOCKET_TIMEOUT))
    logger.info("Validating SOCKET_TIMEOUT: " + str(SOCKET_TIMEOUT))
    assert isinstance(SOCKET_TIMEOUT, (int, float)), "ERROR: SOCKET_TIMEOUT must be a number"
    assert SOCKET_TIMEOUT > 0, "ERROR: SOCKET_TIMEOUT must be positive, got " + str(SOCKET_TIMEOUT)
    print("SOCKET_TIMEOUT is valid: " + str(SOCKET_TIMEOUT))
    logger.info("SOCKET_TIMEOUT is valid: " + str(SOCKET_TIMEOUT))

    print("Validating CONTENT_TYPES dictionary")
    logger.info("Validating CONTENT_TYPES dictionary")
    assert len(CONTENT_TYPES) > 0, "ERROR: CONTENT_TYPES dictionary is empty"
    assert 'html' in CONTENT_TYPES, "ERROR: 'html' must be defined in CONTENT_TYPES"
    print("CONTENT_TYPES dictionary is valid with " + str(len(CONTENT_TYPES)) + " entries")
    logger.info("CONTENT_TYPES dictionary is valid with " + str(len(CONTENT_TYPES)) + " entries")

    print("\n" + "=" * 60)
    print("All validations passed! Starting server...")
    print("=" * 60 + "\n")
    logger.info("\n" + "=" * 60)
    logger.info("All validations passed! Starting server...")
    logger.info("\n" + "=" * 60)

    main()