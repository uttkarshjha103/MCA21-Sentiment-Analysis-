import urllib.request
import json

base = 'http://localhost:8000/api/v1'

# Login
login_data = json.dumps({'email': 'admin@test.com', 'password': 'Admin@123!'}).encode()
req = urllib.request.Request(
    base + '/auth/login',
    data=login_data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
token = json.loads(urllib.request.urlopen(req).read())['access_token']
print('Logged in')

# Build multipart body
boundary = b'Boundary7MA4YWxkTrZu0gW'

with open('bulk_100_comments.csv', 'rb') as f:
    file_content = f.read()

disp = b'Content-Disposition: form-data; name="file"; filename="bulk_100_comments.csv"'
ctype = b'Content-Type: text/csv'

body = (
    b'--' + boundary + b'\r\n' +
    disp + b'\r\n' +
    ctype + b'\r\n\r\n' +
    file_content +
    b'\r\n--' + boundary + b'--\r\n'
)

req = urllib.request.Request(
    base + '/upload/csv',
    data=body,
    headers={
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'multipart/form-data; boundary=Boundary7MA4YWxkTrZu0gW'
    },
    method='POST'
)

result = json.loads(urllib.request.urlopen(req).read())
print('Stored:', result['stored_count'], '/', result['total_comments'])
if result.get('validation_errors'):
    print('Errors:', len(result['validation_errors']))
