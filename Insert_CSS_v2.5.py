import psycopg2
import os
import urllib3
from datetime import datetime
import re

# disable warning for self-signet certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

## VARIABLE

## UAT SS DB
LOGIN_UAT = 'svc_ev' ## login to UAT Superset DataBase
PASSWORD_UAT = 'J6wYc5a_' ## password to UAT superset database
HOST_UAT = 'SMSK02:1543' 
DATABASE_UAT = 'PRAVDA2_DEV' 
SHEMA_UAT = 'public'

source_sreda = 'DEV'
target_sreda = 'UAT' #dev #prod ##Select to import target server #for future funcion
work_dir = "C:\\Users\\USER\\Desktop\\ss_api\\dashb\\CSS_TEST"


CSS_root_dir = os.path.join(work_dir, 'CSS')

os.makedirs(os.path.join(CSS_root_dir, target_sreda), exist_ok=True)

chart_list_dev = os.path.join(CSS_root_dir, 'chart_list_dev.txt')
chart_list_uat = os.path.join(CSS_root_dir, 'chart_list_uat.txt')
log_file = os.path.join(CSS_root_dir, "log.html") 
URI = f'postgresql://{LOGIN_UAT}:{PASSWORD_UAT}@{HOST_UAT}/{DATABASE_UAT}' #URI to connect to Superset database

 
##check connect to DB
try:
    conn_uat = psycopg2.connect(URI)
    cur_uat = conn_uat.cursor() #connect
except:
    print("Can't connect to database")
        
try:
        os.remove(chart_list_uat) # clean chart list uat
except: pass    
    
try:
    os.remove(log_file)
except: pass

def load_list_from_file(filename):        
    with open (filename, 'r') as file:
        line = file.read().strip()
        return re.findall(r"'(.*?)'", line)

def replace_chart_ids(list_dev, list_uat, text):
    mapping = {}
    for item_dev in list_dev:
        number_dev, text_dev = item_dev.split(', ', 1)
        for item_uat in list_uat:
            number_uat, text_uat = item_uat.split(', ', 1)
            if text_dev == text_uat:
                mapping[number_dev] = number_uat
                break
    sorted_ids = sorted(mapping.items(), key=lambda x: -len(x[0]))    
    

    for number_dev, number_uat in sorted_ids:
        # patterns for replace:
        patterns = [
            (rf'#chart-id-{number_dev}\b', f'#chart-id-{number_uat}'),
            (rf'chart-id-{number_dev}\b', f'chart-id-{number_uat}'),
            (rf'chart-id="{number_dev}"', f'chart-id="{number_uat}"'),
            (rf'data-test-chart-id="{number_dev}"', f'data-test-chart-id="{number_uat}"'),
            (rf'chart-id={number_dev}(?![0-9])', f'chart-id={number_uat}') 
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)    
    return text
    
            
## get chart id/name from UAT db SS
cur_uat.execute(f"select concat(id,', ', slice_name) from {SHEMA_UAT}.slices order by id" )
chart_list = cur_uat.fetchall()

with open(chart_list_uat, 'a') as out:
    for i, value in enumerate(chart_list):    
        out.writelines(str(chart_list[i]).replace("(", "").replace(",)"," "))

   
list_dev = load_list_from_file(chart_list_dev) 
list_uat = load_list_from_file(chart_list_uat)    
    
## insert CSS into database
files_ds = [f for f in os.listdir(os.path.join(CSS_root_dir, source_sreda))] # list files into folder
for file in files_ds:
    if file.endswith(source_sreda.lower() + '.css'):
        with open(os.path.join(CSS_root_dir, source_sreda, file), encoding="utf-8") as CSS:
            CSS = CSS.read()
            CSS = CSS.replace("'","''")  
            CSS = replace_chart_ids(list_dev, list_uat, CSS)
            cur_uat.execute(f"update {SHEMA_UAT}.dashboards set css ='{CSS}' where dashboard_title = '{('_'.join(file.split('_')[:-1]))}'")
        file = file.replace(source_sreda.lower(), target_sreda.lower())
        with open(os.path.join(CSS_root_dir, target_sreda, file), 'w', encoding='utf-8') as out_CSS:
            out_CSS.write(CSS)
conn_uat.commit()
        
cur_uat.close()
conn_uat.close()            