import sys
sys.path.append('C:\\PA-Functions')

import csv
import json
import time
import datetime
import pathlib
import requests
import zipfile
import os
from html.parser import HTMLParser
import re
from datetime import date
import datetime
import shutil
import gspread

from web_functions import WebFunctions
from db_functions import DBCalls
from google_functions import GoogleFunctions

cred = CredVariables("MIRROR")
google = GoogleFunctions(
    "Brandon.Hernandez@prontoinsurance.com",
    cred.google_smtp_password
)
web_functions = WebFunctions()
db_functions = DBCalls(
    cred.oracle_username,
    cred.oracle_password,
    cred.oracle_ip,
    cred.oracle_servicename,
    cred.replica_connection_string
)