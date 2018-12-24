# standard python imports
import argparse
import csv
from datetime import datetime
import multiprocessing
import os
import pickle
from sys import exit
import webbrowser

# third parties imports
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# package imports
import utils


def drive_batch_callback(request_id, response, exception):
    if exception:
        # Handle error
        print("Error in batch sharing. request_id: {}, response: {}, exception: {}".format(request_id, response,
                                                                                           exception))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Checks domains to see if they belong to a known console.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # domains to be checked can be read either from a csv file or from the command line
    domains_group = parser.add_mutually_exclusive_group(required=False)
    domains_group.add_argument('-cf', '--csv-file', type=str, nargs=1, default='domains_list.csv',
                               help='a csv file containing a list of domains to be checked')
    domains_group.add_argument('-d', '--domains', type=str, nargs='+', help='domains to be checked', metavar='DOMAIN')

    # path to the client secret file downloaded from the developer console
    parser.add_argument('-cs', '--client-secret', type=str, nargs=1, default=['client_secret_domain_check.com.json'],
                        metavar='JSON', help='path to the client secret file exported from the developer console')

    # we have to decide where to write the output results
    output_group = parser.add_mutually_exclusive_group(required=False)
    # csv output file, we do not use argpars.FileType as we can't pass the newline parameter
    output_group.add_argument('-of', '--output-file', type=str, nargs=1, default='domain_info.csv',
                              help='path to a csv file to write extracted information')
    # in as spreadsheet
    output_group.add_argument('-td', '-todrive', type=str, nargs='*', metavar='SHARE',
                              help='store the results in a google sheet and share it with one or more account')

    # how many parallel process do we want to spawn?
    parser.add_argument('-pn', '--process-number', type=int, default=4,
                        help='number of concurrent processes to spawn; WARNING: an high number can trigger google '
                             'serving limits!')

    args = parser.parse_args()

    # sanity check on process numbers
    if args.process_number <= 0:
        raise argparse.ArgumentError(args.process_number, 'vaule must be bigger than zero!')

    # queues to manage the parallel processing of domains
    tasks = multiprocessing.JoinableQueue()
    domains_info = multiprocessing.Queue()

    # we want to be sure that domains are initialized, even if empty
    domains = []

    # if d parameter is present we use it otherwise we check for a csv file
    if args.domains is not None:
        domains = [domain for domain in args.domains]
    elif args.csv_file is not None:
        try:
            with open(args.csv_file[0], 'r') as csv_input:
                domain_reader = csv.reader(csv_input)
                domains = [row[0] for row in domain_reader]
        except FileNotFoundError as e:
            # if we can not open the domain csv file we exit from the program printing the help
            parser.print_help()
            exit()
    else:
        raise ValueError("Input domains must be provided either with -cf or -d parameters.")

    # if no domains are found we exit from the script
    if not domains:
        print('No domains found!\n\n')
        parser.print_help()
        exit()

    # Scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file',
              'https://www.googleapis.com/auth/apps.order.readonly', ]

    # START ID CREDENTIAL FLOW
    if not os.path.exists('credentials.dat'):

        flow = InstalledAppFlow.from_client_secrets_file(args.client_secret[0], SCOPES)
        credentials = flow.run_local_server()

        with open('credentials.dat', 'wb') as credentials_dat:
            pickle.dump(credentials, credentials_dat)
    else:
        with open('credentials.dat', 'rb') as credentials_dat:
            credentials = pickle.load(credentials_dat)

    if credentials.expired:
        credentials.refresh(Request())

    # we spawn the processes
    consumers = [utils.Consumer(tasks, domains_info, SCOPES, args.client_secret[0])
                 for i in range(args.process_number)]

    # we start the processes
    for d in consumers:
        d.start()

    # export headers
    fieldnames = ['domain', 'customerId', 'customerDomain', 'error', 'errorCode', 'errorMessage']

    # enqueuing of domains to the consumer
    for to_check in domains:
        tasks.put(utils.DomainChecker(to_check))

    # Add a poison pill for each consumer
    for i in range(args.process_number):
        tasks.put(None)

    # Wait for all of the tasks to finish
    tasks.join()

    # once we're done we move all the results in a list
    results = []
    while not domains_info.empty():
        results.append(domains_info.get())

    # should we write to drive?
    if args.td is not None:
        current_time = datetime.now().strftime("%Y%m%d")
        tab_name = 'Domains'

        # to write in drive we need an array of strings, we start with the header
        plain_data = [fieldnames]

        # ... and we normalize the results data
        for info in results:
            sheet_row = [info[key] for key in plain_data[0]]
            plain_data.append(sheet_row)

        # creation parameters for the spreadsheet
        create_body = {
            'properties': {
                'title': '[INTERNAL][Revevol][{}] G Suite Deployment - Domains Checker - EN'.format(current_time),
                'locale': 'it_IT',
                'timeZone': 'Europe/Rome'
            },
            'sheets': [
                {
                    'properties': {
                        'sheetId': 0,
                        'title': tab_name,
                        'index': 0,
                        'sheetType': 'GRID',
                        'gridProperties': {
                            'rowCount': len(plain_data) + 1,
                            'columnCount': len(plain_data[0]),
                        },
                    },
                    'data': [
                        {
                            'startRow': 0,
                            'startColumn': 0,
                            'rowData': [
                                {
                                    'values': [
                                        {

                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        update_body = {
            'values': plain_data,
        }

        spreadsheet_sdk = build('sheets', 'v4', credentials=credentials)
        report_ss = spreadsheet_sdk.spreadsheets().create(body=create_body).execute()

        update_body_params = {
            'spreadsheetId': report_ss['spreadsheetId'],
            'range': '{}!A1'.format(tab_name),
            'body': update_body,
            'valueInputOption': 'USER_ENTERED',
        }

        # we populate the spreadsheet with the domains info
        update_ss = spreadsheet_sdk.spreadsheets().values().update(**update_body_params).execute()

        header_update_req = {
            'spreadsheetId': report_ss['spreadsheetId'],
            'body': {
                'requests': [
                    {
                        'updateSheetProperties': {  # freeze first row
                            'properties': {
                                'gridProperties': {
                                    'frozenRowCount': 1
                                }
                            },
                            'fields': 'gridProperties.frozenRowCount'
                        }
                    },
                    {
                        'repeatCell': {  # make the first row bold
                            'range': {
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'textFormat': {
                                        'bold': True
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat.textFormat.bold'
                        }
                    },
                    {
                        'setBasicFilter': {  # add the filter
                            'filter': {
                                'range': {
                                    'sheetId': 0
                                }
                            }
                        }
                    }
                ]
            }
        }

        update_ss2 = spreadsheet_sdk.spreadsheets().batchUpdate(**header_update_req).execute()

        print("Generated spreadsheet available at: {}".format(report_ss['spreadsheetUrl']))
        if len(args.td) == 0:
            # we finally open the result in a browser
            webbrowser.open(report_ss['spreadsheetUrl'], new=2, autoraise=True)
        else:
            # we share the file with people
            drive_sdk = build('drive', 'v3', credentials=credentials)
            batch = drive_sdk.new_batch_http_request(callback=drive_batch_callback)

            for email_to_share in args.td:
                user_permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': email_to_share,
                }
                batch.add(drive_sdk.permissions().create(
                    fileId=report_ss['spreadsheetId'],
                    body=user_permission,
                    fields='id',
                    emailMessage="Please find enclosed the verification status for the following domains:\n{}".format(
                        "\n".join(domains)),
                ))

            batch.execute()
    # we write a csv file
    else:
        with open(args.output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')

            writer.writeheader()
            writer.writerows(results)
