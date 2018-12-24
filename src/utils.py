# built-in imports
import json
import multiprocessing
import os
import pickle

# third parties import
import googleapiclient.errors
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class Consumer(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, scopes, client_secret):
        multiprocessing.Process.__init__(self)

        self.task_queue = task_queue
        self.result_queue = result_queue

        self._scopes = scopes
        self._client_secret = client_secret

        # START ID CREDENTIAL FLOW
        if not os.path.exists('credentials.dat'):

            self._flow = InstalledAppFlow.from_client_secrets_file(self._client_secret, self._scopes)
            self._credentials = self._flow.run_local_server()

            with open('credentials.dat', 'wb') as credentials_dat:
                pickle.dump(self._credentials, credentials_dat)
        else:
            with open('credentials.dat', 'rb') as credentials_dat:
                self._credentials = pickle.load(credentials_dat)

        if self._credentials.expired:
            self._credentials.refresh(Request())

        self._reseller_sdk = build('reseller', 'v1', credentials=self._credentials)

    def run(self):

        while True:
            if self._credentials.expired:
                self._credentials.refresh(Request())
                self._reseller_sdk = build('reseller', 'v1', credentials=self._credentials)

            next_task = self.task_queue.get()
            # print(next_task)

            if next_task is None:
                # Poison pill means shutdown
                # print ('{}: Exiting'.format(proc_name))
                self.task_queue.task_done()
                break

            # print("{}: {}".format(proc_name, next_task))

            answer = next_task(self._reseller_sdk)

            self.task_queue.task_done()

            try:
                self.result_queue.put(answer)
            except Exception as e:
                print(e)
        return


class DomainChecker:
    def __init__(self, domain):

        self.domain = domain.lower()

    def __call__(self, reseller_sdk):

        domain_check_params = {
            'customerId': self.domain,
        }

        # dictionary to store the data
        customer_info = {
            'domain': self.domain,
            'customerId': '',
            'customerDomain': '',
            'error': 'N',
            'errorCode': '',
            'errorMessage': '',
        }

        try:
            customer_response = reseller_sdk.customers().get(**domain_check_params).execute()
            customer_info['customerId'] = customer_response['customerId']
            customer_info['customerDomain'] = customer_response['customerDomain']
        except googleapiclient.errors.HttpError as error:
            error_data = json.loads(error.content)
            customer_info['error'] = 'Y'
            customer_info['errorCode'] = error_data['error']['code']
            customer_info['errorMessage'] = error_data['error']['message']
        finally:
            print("Info: {}".format(customer_info))

        return customer_info

    def __str__(self):
        return "DomainChecker for domain: {}".format(self.domain)
