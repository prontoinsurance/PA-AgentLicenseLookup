import sys
import time

sys.path.append('C:\\PA-Functions')

import json
import pathlib
from datetime import datetime
import threading

from web_functions import WebFunctions
from db_functions import DBCalls
from CredentialDefinitions import CredVariables
from google_functions import GoogleFunctions

cred = CredVariables()
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
                                                     google_spreadsheet_url=cred.google_sheet_url)
    return google_service, google_sheet_link


def load_sircon():
    browser = web_functions.icongito_web_driver_download()
    web_functions.web_wait(5)
    browser = web_functions.startup_browser(browser, cred.sircon_compliance_website)
    web_functions.web_wait(5)
    browser = web_functions.sircon_proceed_check_webpage(browser)
    web_functions.web_wait(8)
    return browser


def setup_search_sircon(browser):
    browser = web_functions.sircon_select_state_search(browser)
    web_functions.web_wait()
    return browser


def process_google_sheet_data(google_sheet_link):
    # google_sheet_data = google.get_all_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_license_status, json_format=True)
    agent_google_sheet_data = db_functions.get_agent_license_status([None])

    if agent_google_sheet_data is not None and agent_google_sheet_data != []:

        data_list = []

        for data in agent_google_sheet_data:
            data_list.append(list(data))

        if data_list is not None and len(data_list) != 0:
            google.delete_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_license_status)
            google.add_google_sheet_data(google_sheet_link, data_list, True, cred.google_sheet_agent_license_status)

    return None


def process_google_sheet_data_individual(google_sheet_link):
    # google_sheet_data = google.get_all_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_license_status, json_format=True)
    agent_google_sheet_data = db_functions.get_agent_individual_status([None])

    if agent_google_sheet_data is not None and agent_google_sheet_data != []:

        data_list = []

        for data in agent_google_sheet_data:
            data_list.append(list(data))

        if data_list is not None and len(data_list) != 0:
            google.delete_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_lookup_individual)
            google.add_google_sheet_data(google_sheet_link, data_list, True, cred.google_sheet_agent_lookup_individual)

    return None


def process_google_sheet_data_appointment(google_sheet_link):
    # google_sheet_data = google.get_all_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_license_status, json_format=True)
    agent_google_sheet_data = db_functions.get_agent_appointment_status([None])
    if agent_google_sheet_data is not None and agent_google_sheet_data != []:

        data_list = []

        for data in agent_google_sheet_data:
            data_list.append(list(data))

        if data_list is not None and len(data_list) != 0:
            google.delete_data_from_spreadsheet(google_sheet_link, cred.google_sheet_agent_lookup_appointment)
            google.add_google_sheet_data(google_sheet_link, data_list, True, cred.google_sheet_agent_lookup_appointment)

    return None


def thread_function(agent_lookup_data, google_sheet_link, thread_number):
    browser = None
    try:
        browser = load_sircon()

        browser = setup_search_sircon(browser)

        browser = web_functions.sircon_select_individual_search(browser)

        thread_index = 1

        for agent in agent_lookup_data:

            print("Thread # " + str(thread_number) + " Processing : " + str(thread_index) + " out of " + str(
                len(agent_lookup_data)))

            # if thread_index % 200 == 0:
            #     process_google_sheet_data(google_sheet_link)
            #     process_google_sheet_data_individual(google_sheet_link)
            #     process_google_sheet_data_appointment(google_sheet_link)

            browser = web_functions.sircon_add_license_search_info(browser, agent["LicenseNumber"])

            # At this point it should be on the screen
            browser, individual_data, data_returned = web_functions.sircon_get_individual_date(browser)

            time.sleep(2)

            if data_returned:
                # Add a try here since if succesful this will break
                browser, appointment_data = web_functions.sircon_agency_lookup(browser, "Redpoint County Mutual Insurance Company")

                db_functions.insert_agent_websnapshot(
                    [json.dumps(individual_data), json.dumps(appointment_data), agent["AgentImportId"]])

                if appointment_data == [] or individual_data == []:
                    db_functions.update_agent_license_processing([agent["AgentImportId"], True, False, None])
                else:
                    db_functions.update_agent_license_processing([agent["AgentImportId"], True, data_returned, None])

                log_information(note="Thread # " + str(thread_number) + ' Success DateBatchId : ' + datetime.now().strftime('%Y%m%d') + ' Agent Import Id : ' + str(
                    agent["AgentImportId"]), failure_bit=0)

            else:
                db_functions.update_agent_license_processing([agent["AgentImportId"], True, data_returned, None])

                log_information(note="Thread # " + str(thread_number) + ' Failure DateBatchId : ' + datetime.now().strftime('%Y%m%d') + ' Agent Import Id : ' + str(
                    agent["AgentImportId"]), failure_bit=1)

            thread_index += 1

        process_google_sheet_data(google_sheet_link)
        process_google_sheet_data_individual(google_sheet_link)
        process_google_sheet_data_appointment(google_sheet_link)

    except Exception as e:
        print("Error occurred during processing " + str(e))
    finally:
        if browser:
            browser.quit()

    return None


def main():
    # Create the file paths needed for screenshots
    create_screenshot_file_paths()

    try:
        google_service, google_sheet_link = setup_google_connection()
    except Exception as w:
        log_information(note='Failure to connect to Google: ' + str(w)[0:900], failure_bit=1)

    # function to get claims that will
    oracle_json_data = db_functions.get_pulse_agent_lookup()
    if oracle_json_data != [] and oracle_json_data is not None:
        db_functions.insert_agent_import([oracle_json_data, "Pulse"])

    agent_lookup_data = db_functions.get_agent_import_data()
    db_functions.insert_agent_license_processing(None)

    process_google_sheet_data(google_sheet_link)
    process_google_sheet_data_individual(google_sheet_link)
    process_google_sheet_data_appointment(google_sheet_link)

    # for agent in agent_google_sheet_data:
    #     agent_data = list(agent)
    #     google.update_google_sheet_row_by_id(google_sheet_link, agent_data[0], agent_data[1:], True, cred.google_sheet_agent_license_status)

    if len(agent_lookup_data) != 0:
        if len(agent_lookup_data) >= 2:
            list_size = len(agent_lookup_data) // 2
        else:
            list_size = agent_lookup_data

        agent_chunks = [agent_lookup_data[i:i + list_size] for i in range(0, len(agent_lookup_data), list_size)]

        threads = []
        for agent_list in agent_chunks:
            thread = threading.Thread(target=thread_function, args=(agent_list, google_sheet_link, len(threads)+1,))
            threads.append(thread)
            thread.start()
            time.sleep(120)

        for thread in threads:
            thread.join()

        process_google_sheet_data(google_sheet_link)
        process_google_sheet_data_individual(google_sheet_link)
        process_google_sheet_data_appointment(google_sheet_link)
    else:
        print("No data")


    # Have to comment out due to google quota limit need to do a full refresh only once and a while
    # google_sheet_data = db_functions.get_agent_processed_individual_by_id([agent["AgentImportId"]])
    # for google_data in google_sheet_data:
    #     data_list = list(google_data)
    #
    #     print(str(data_list[0]))
    #
    #     google.update_google_sheet_row_by_id(google_sheet_link, data_list[0], data_list[1:], True,
    #                                          cred.google_sheet_agent_lookup_individual)
    #
    #     print("should be updated")


if __name__ == "__main__":
    main()
