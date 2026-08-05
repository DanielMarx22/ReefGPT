import os
import urllib.request
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

res = supabase.table("metrics_log").select("timestamp").order("timestamp", desc=True).limit(1).execute()
print(f"Latest timestamp in DB: {res.data[0]['timestamp'] if res.data else 'None'}")

req = urllib.request.Request("http://192.168.4.21/cgi-bin/datalog.xml")
with urllib.request.urlopen(req, timeout=10) as response:
    xml_data = response.read().decode('utf-8')
    
root = ET.fromstring(xml_data)
records = root.findall('record')
if records:
    print(f"Earliest in Apex XML: {records[0].find('date').text}")
    print(f"Latest in Apex XML: {records[-1].find('date').text}")
