from flask import Flask, request, jsonify, make_response
import yaml
import logging, os
import requests
import datetime
import json
import xml.etree.ElementTree as ET

app = Flask(__name__)

config = yaml.safe_load(open("config.yml"))

#region Global variables
COMPANY = config["COMPANY"]
API_URL = config["API_URL"]
PRIORITY_API_USERNAME= config["PRI_API_USERNAME"]
PRIORITY_API_PASSWORD= config["PRI_API_PASSWORD"]
EXTRA_FIELDS = config["EXTRA_FIELDS"]
#endregion

# Set up error logger.
path = r"error.log"
assert os.path.isfile(path)
logging.basicConfig(filename=path, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('Flask server started.')

#region Endpoint definitions
@app.route("/webfeed/")
def home():
    return "This is the Flask App on IIS Server to serve Web Feed."

@app.route("/webfeed/invoices")
def invoices():
    page = request.args.get('page', default = 1, type = int)
    len = request.args.get('len', default = 10, type = int)
    custname = request.args.get('custname', type = str)
    r = requests.get(f"{API_URL}{COMPANY}/CINVOICES?$filter=CUSTNAME eq '{custname}'&$top={len}&$skip={page}&$select=CUSTNAME,IVNUM,DISPRICE,{EXTRA_FIELDS}",  auth=(PRIORITY_API_USERNAME, PRIORITY_API_PASSWORD))
    print(f"{API_URL}{COMPANY}/CINVOICES?$filter=CUSTNAME eq '{custname}'&$top={len}&$skip={page}&$select=CUSTNAME,IVNUM,DISPRICE,{EXTRA_FIELDS}")
    data = r.json()['value']
    
    # Create root XML element
    root = ET.Element("V_RSINV")
    root.set("Customer", data[0]["CUSTNAME"])
    root.set("invtype", "A")
    # root.set("ResultCount", str(len(data)))
    root.set("page", str(page))
    root.set("len", str(len))

    # Calculate start and end indices based on page and page length
    start_index = (page - 1) * len
    end_index = start_index + len

    extra_field_keys = EXTRA_FIELDS.split(",")
    
    # Add sub-elements to root element
    for i, item in enumerate(data, start=start_index + 1):
        record = ET.SubElement(root, "record")
        record.set("Recordid", str(i))
        record.set("CUSTNAME", item["CUSTNAME"])
        record.set("IVNUM", item["IVNUM"])
        record.set("DISPRICE", "{:.4f}".format(item["DISPRICE"]))
        # For extra fields 
        for key in extra_field_keys:
            record.set(key, str(item[key]))
        record.set("TIMESTAMP", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        record.set("PAYDATE", datetime.date.today().replace(day=1).strftime("%Y-%m-%dT%H:%M:%S"))
        
            
    # Convert ElementTree object to XML string
    xml_string = ET.tostring(root)

    # Print XML string
    response = make_response(xml_string.decode())
    response.headers['Content-Type'] = 'application/xml'

    return response
#endregion