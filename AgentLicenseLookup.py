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
from CredentialDefinitions import CredVariables
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

PROCESS_ID = 4


def create_screenshot_file_paths():
    if not pathlib.Path(cred.error_screenshot_file_path).exists():
        # log file will only create the error log and date if needed
        pathlib.Path(cred.error_screenshot_file_path).mkdir(parents=True, exist_ok=True)

    if not pathlib.Path(cred.success_screenshot_file_path).exists():
        # log file will only create the error log and date if needed
        pathlib.Path(cred.success_screenshot_file_path).mkdir(parents=True, exist_ok=True)


def log_information(note, failure_bit):
    # If the letter status needs to update then pass update_status otherwise just sent note and failure bit
    db_functions.insert_run_log([PROCESS_ID, note, failure_bit])

    return None


def setup_google_connection():
    google_service, google_spreadsheet = google.authorize_json(cred.google_cred_json_file_path)
    # We need the google sheet link
    google_sheet_link = google.get_google_sheet_link(google_spreadsheet=google_spreadsheet,
                                                     google_spreadsheet_url=cred.google_sheet_url,
                                                     sheet_worksheet_name=cred.claim_pd_worksheet_name)
    return google_service, google_sheet_link


def load_sircon():
    browser = web_functions.web_driver_download()
    web_functions.web_wait()
    browser = web_functions.startup_browser(browser, cred.sircon_compliance_website)
    web_functions.web_wait()
    browser = web_functions.sircon_proceed_check_webpage(browser)
    web_functions.web_wait(10)
    return browser

def main():
    # Create the file paths needed for screenshots
    create_screenshot_file_paths()

    try:
        google_service, google_sheet_link = setup_google_connection()
    except Exception as w:
        log_information(note='Failure to connect to Google: ' + str(w)[0:900], failure_bit=1)

    # function to get data here which will load data into tables

    # function to get claims that will

    browser = load_sircon()





if __name__ == "__main__":
    main()
