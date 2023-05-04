import base64
import zipfile

def unzip_and_encode(file_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('.')
    with open('packages.json', 'rb') as f:
        encoded = base64.b64encode(f.read())
    return encoded

def main():
    file_path = '/Users/colleengranelli/Documents/unzip/packages.json.zip'
    encoded_data = unzip_and_encode(file_path)
    print(encoded_data)

if __name__ == '__main__':
    main()

