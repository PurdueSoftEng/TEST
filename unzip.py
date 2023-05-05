import base64
import zipfile
import io

def unzip_and_encode(file_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('.')
    with open('packages.json', 'rb') as f:
        encoded = base64.b64encode(f.read())
    return encoded


def package_json_fetch(content):
    try:
        bin = base64.b64decode(content)
    except:
        bin = base64.b64decode(content + '===')
    zf = zipfile.ZipFile(io.BytesIO(bin))
    try:
        obj = zf.getinfo("package.json")
        with zf.open("package.json", 'r') as ptr:
            contents = ptr.read().decode('utf-8')
            return json.loads(contents)
    except:
        return None


            


def main():
    file_path = 'lodash_base64'
    with open(file_path, 'r') as ptr:
        content = ptr.read()
    package_json_fetch(content)
    #encoded_data = unzip_and_encode(file_path)

if __name__ == '__main__':
    main()

