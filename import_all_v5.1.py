###import
import requests
import shutil
import os
import zipfile
import subprocess
import re
import urllib3

# disable warning for self-signet certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

# variable for work
SUPERSET_DOMAIN = "https://HOST:PORT"
SUPERSET_USERNAME = "LOGIN"
SUPERSET_PASSWORD = "PASS"
INPUT_DIR = "C:\\Users\\USERNAME\\Desktop\\ss_api\\dashb" # work directory
DATABASE_NAME = "DB_NAME.yaml"  # View the contents of EXPORTED_ZIP_FILE to get this name!
DATABASE_PASSWORD = "PASS_FOR_DATABASE" # use in first import


# variable for replace dev -> prod conn/catalog 
db_dev_link = 'postgresql://USER:PASS@HOST:PORT/DB'
db_uat_link = 'postgresql://USER:PASS@HOST:PORT/DB_PROD'
db_name = 'DB'
ds_dev = 'DATASET_DEV'
ds_uat = 'DATASET_UAT'
output_filename = os.path.join(INPUT_DIR, "out.log")

session = requests.session()


## set payload parameters
payload={
            'overwrite': 'true',
            'passwords': '{"databases/' + DATABASE_NAME +'": "' + DATABASE_PASSWORD + '"}'
        }

## get access token
endpoint = "/api/v1/security/login"
url = f"{SUPERSET_DOMAIN}{endpoint}"
jwt_token =session.post(
    url = f"{SUPERSET_DOMAIN}{endpoint}",
    json={
        "username": SUPERSET_USERNAME,
        "password": SUPERSET_PASSWORD,
        "provider": "ldap", #if use LDAB. If use DB autoriz - change this to ' "provider": "db" '
        "refresh": False
        } ,
    verify = False  
)
if jwt_token.status_code != 200:
    Exception(f"Got HTTP code of {jwt_token.status_code} from {url}; expected 200")
else:
    jwt_token = jwt_token.json()["access_token"]


## get csrf token
endpoint = "/api/v1/security/csrf_token"
url = f"{SUPERSET_DOMAIN}{endpoint}"
csrf_token = session.get(
    url,
    headers = {
        "Authorization": f"Bearer {jwt_token}"
        }, 
    verify = False
)
if csrf_token.status_code != 200:
    print(Exception(f"Got HTTP code of {csrf_token.status_code} from {url}; expected 200"))
else:
    csrf_token = csrf_token.json()["result"]


def import_object(file_name, database_name, database_password, endpoint):
    url = f"{SUPERSET_DOMAIN}{endpoint}"
    with open(os.path.join(INPUT_DIR,file_name), 'rb') as infile:
        files = {'formData': ('zip', infile.read(), 'application/zip')}
    response = session.post(
        url, 
        verify = False,
        headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {jwt_token}',
                'X-CSRFToken': csrf_token,
                'Referer': SUPERSET_DOMAIN    
                },
        files=files,
        data=payload
    )
    os.remove(os.path.join(INPUT_DIR,file_name))
    print(file_name+ ' imported successfully')

# Ensure we got the expected 200 status code
    if response.status_code != 200:
        raise Exception(
            f"Got HTTP code of {response.status_code} from {url}; expected 200.  See {output_filename} or server logs for possible hints"
        )

# Ensure we can parse the response as JSON
    try:
        response_json = response.json()
    except Exception as exception:
        raise Exception(f"Could not parse response from {url} as JSON (see {output_filename} or server logs for possible hints)")

# Ensure that the JSON has a 'message' field
    try:
        message = response_json["message"]
    except KeyError as exception:
        raise Exception(f"Could not find 'message' field in response from {url}, got {response_json}")

# Ensure that the 'message' field contains 'OK'
    if message != "OK":
        raise Exception(f"Got message '{message}' from {url}; expected 'OK'")

def create_zip(INPUT_DIR, rep_name, out_zip):# add files to ZIP
            for folder, subfolders, files in os.walk(os.path.join(INPUT_DIR, rep_name ) +'_unp'):
                for file in files:
                    out_zip.write(os.path.join(folder, file), 
                                os.path.relpath(os.path.join(folder,file),
                                    (os.path.join(INPUT_DIR, rep_name ) +'_unp')), compress_type = zipfile.ZIP_DEFLATED)
            out_zip.close()
            
def edit_meta(work_path, files_ds, old_type, new_type):
            for i in range(0, len(files_ds)):
                 with open (os.path.join(work_path, os.listdir(work_path)[0], 'metadata.yaml')) as metadata_old:
                     metadata = metadata_old.read()
                 metadata_new = metadata.replace(old_type, new_type)
                 with open(os.path.join(work_path, os.listdir(work_path)[0], 'metadata.yaml'), "w") as db_conn_out:
                     db_conn_out.write(metadata_new)


files_ds = [f for f in os.listdir(INPUT_DIR)]

for file_name in files_ds: # unpack source archive
    if file_name.endswith('.zip') and not file_name.endswith('for_load.zip') and file_name.startswith('dashb'):
        rep_name = file_name.strip('.zip')
        with zipfile.ZipFile(os.path.join(INPUT_DIR, file_name), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(INPUT_DIR, (rep_name + '_unp')))
        
            work_path = os.path.join(INPUT_DIR, (rep_name + '_unp'))

             # edit source data                    
            files = [f for f in os.listdir(work_path)]
            db_path = os.path.join(work_path, files[0], 'databases')
            ds_path = os.path.join(work_path, files[0], 'datasets', db_name)
            dash_path = os.path.join(work_path,files[0], 'dashboards')
            
            files_dash = [f for f in os.listdir(dash_path)]            
            
            if os.path.exists(dash_path):
                for i in range(0, len(files_dash)): # delete CSS
                    with open (os.path.join(dash_path, files_dash[i])) as inp_dash:
                        inp_dash = inp_dash.read()                    
                    re_dash = re.sub(r'css:.*?slug:', 'slug:', inp_dash, flags=re.DOTALL)                    
                    with open (os.path.join(dash_path, files_dash[i]), 'w') as old_dash:
                        old_dash.write(re_dash)             

            if os.path.exists(db_path):
                files_db = [f for f in os.listdir(db_path)] # change connection string            
                for i in range(0, len(files_db)):
                    with open (os.path.join(db_path, files_db[i])) as db_conn:
                        prod_conn = db_conn.read()
                    prod_conn = prod_conn.replace(db_dev_link, db_uat_link)    
                    with open(os.path.join(db_path ,files_db[i]), "w") as db_conn_out:
                        db_conn_out.write(prod_conn)  
                                 
            if os.path.exists(ds_path):
                files_ds = [f for f in os.listdir(ds_path)] # change catalog in datasets       
                for i in range(0, len(files_ds)):
                    with open(os.path.join(ds_path, files_ds[i])) as dataset_dev:
                        dataset_edit = dataset_dev.read()
                    dataset_edit = dataset_edit.replace(ds_dev, ds_uat)
                    with open(os.path.join(ds_path, files_ds[i]), "w") as dataset_uat:
                        dataset_uat.write(dataset_edit) 
                # end edit datasource  
            
            # repack object into ZIP 
            if os.path.exists(dash_path):
                out_zip = zipfile.ZipFile((os.path.join(INPUT_DIR, (rep_name )) +'_for_load.zip'), 'w')
                create_zip(INPUT_DIR, rep_name, out_zip)  # repack dash 
                shutil.rmtree(os.path.join(work_path, os.listdir(work_path)[0], 'dashboards'))
            
            edit_meta(work_path, files_ds, 'Dashboard', 'Slice')
            if os.path.exists(os.path.join(work_path, os.listdir(work_path)[0], 'charts')):
                out_zip = zipfile.ZipFile((os.path.join(INPUT_DIR, ('chart_' + rep_name )) +'_for_load.zip'), 'w')
                create_zip(INPUT_DIR, rep_name, out_zip)    # new ZIP without dash 
                shutil.rmtree(os.path.join(work_path, os.listdir(work_path)[0], 'charts'))
            
            edit_meta(work_path, files_ds, 'Slice','SqlaTable')
            edit_meta(work_path, files_ds, 'Dashboard', 'SqlaTable')
            if os.path.exists(os.path.join(work_path, os.listdir(work_path)[0], 'datasets')):
                out_zip = zipfile.ZipFile((os.path.join(INPUT_DIR, ('dataset_' + rep_name )) +'_for_load.zip'), 'w')
                create_zip(INPUT_DIR, rep_name, out_zip) # new ZIP with dataset only
            
        try:
            shutil.rmtree(os.path.join(INPUT_DIR, rep_name ) +'_unp')
        except OSError as e:
            with open(output_filename, "wt", encoding="utf-8") as outfile:
                outfile.write(e)

#import process
files_ds = [f for f in os.listdir(INPUT_DIR)]
for file_name in files_ds:
    if file_name.endswith('for_load.zip'):     
        if file_name.startswith('dash'): 
            endpoint = "/api/v1/dashboard/import/"
        elif file_name.startswith('chart'):
            endpoint = "/api/v1/chart/import/"
        elif file_name.startswith('dataset'):
            endpoint = "/api/v1/dataset/import/"
        else:
            continue
    
        import_object(file_name, DATABASE_NAME, DATABASE_PASSWORD, endpoint)


session.close()


