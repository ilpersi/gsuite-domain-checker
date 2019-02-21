# G Suite domain checker
[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=DH7984HPJ8C4N&currency_code=EUR&source=url)

## What is G Suite domain checker?
gsuite-domain-checker is a simple python CLI utility to check the status of domains to verify if they belong to any G Suite console

## Features
gsuite-domain-checker is able to:
* check an high number of domains using python multiprocessing module
* read input domain list both from command line parameters or using a csv input file
* generate the output result in csv format or in a Google Spreadsheet
* if the Google spreadsheet format is used, using options it can be automatically shared with the desired recipients

## Requirements
To be able to use this script you need:
* to have [access to a G Suite reseller console](https://support.google.com/a/answer/142231?hl=en)
* a Google developer project with the following APIs enabled
  * [G Suite Reseller API](https://developers.google.com/admin-sdk/reseller/v1/get-start/getting-started): these APIs will be used with a __read only__ scope to get information about the domains
  * [Google Drive API](https://developers.google.com/drive/): these APIs are used, based on the parameters, to create Google Spreadsheets used as output for the domains information and to share them with the desired recipients. This will only grant access to files created using gsuite-domain-checker.
  * [Google Sheets API](https://developers.google.com/sheets/): these APIs are used to interact with sheets holding the output information

## Important
This script has only been tested with python 3.6 so I strongly recommend to use that version of the python interpreter or a following one.
  
## First time use
If you are not familiar with the [Google API console](https://console.developers.google.com/) I recommend you to read some documentation before attempting this.

Here are the main steps:
* Create a new project ([here](https://cloud.google.com/resource-manager/docs/creating-managing-projects?visit_id=636812630402595025-4052861048&rd=1) for more details):
  * Go to the [Manage resources page](https://console.cloud.google.com/cloud-resource-manager) in the GCP Console
  * Create a new project. Be sure to note down the name you give to your project 
* Enable the required APIs
  * Open the [Library page](https://console.developers.google.com/apis/library) in the API Console
  * Make sure that in the top left dropdown the selected project is the one you just created. If it is not, switch to it.
  * Search and Enable the following APIs
    * Google Apps Reseller API
    * Google Drive API
    * Google Sheets API
* Create Credentials
  * Open the [Credentials page](https://console.developers.google.com/apis/credentials)
  * Make sure that in the top left dropdown the selected project is the one you just created. If it is not, switch to it.
  * From the center "Create credentials" drop menu choose _OAuth client ID_
  * If prompted to do so Configuare your consent screen
    * Click the _Configuare consent screen_ button
    * Fill the _Application name_ field
    * click the save button at the bottom of the page (yes, you can leave the rest of the info blank)
  * choose _Other_ as Application type
  * Type your desired name for the credentials (note it down, as you will use it) and click the create button. Read the upcoming pop-up and dismiss it with the OK button
  * You now need to download the JSON file for the credentials you've just created.
  To do so, next to the credentials you just created click the Download JSON button (the arrow pointing down) and save the newly created file in your directory of choice.
  Be sure to take note of where you save this file, you will need it to run the tool: this is the client secret file required by the tool (refer to the -cs parameters in the documentation below).  

## Commands
Below you can find the documentation of the CLI parameters used to run the tool. For simple usage just use the -d parameter with the desired domain.

    usage: gsuite_domain_checker.py [-h] [-cf CSV_FILE | -d DOMAIN [DOMAIN ...]]
                                    [-cs JSON]
                                    [-of OUTPUT_FILE | -td [SHARE [SHARE ...]]]
                                    [-pn PROCESS_NUMBER]
    
    Checks domains to see if they belong to a known console.
    
    optional arguments:
      -h, --help            show this help message and exit
      -cf CSV_FILE, --csv-file CSV_FILE
                            a csv file containing a list of domains to be checked
                            (default: domains_list.csv)
      -d DOMAIN [DOMAIN ...], --domains DOMAIN [DOMAIN ...]
                            domains to be checked (default: None)
      -cs JSON, --client-secret JSON
                            path to the client secret file exported from the
                            developer console (default:
                            client_secret_domain_check.com.json)
      -of OUTPUT_FILE, --output-file OUTPUT_FILE
                            path to a csv file to write extracted information
                            (default: domain_info.csv)
      -td [SHARE [SHARE ...]], -todrive [SHARE [SHARE ...]]
                            store the results in a google sheet and share it with
                            one or more account (default: None)
      -pn PROCESS_NUMBER, --process-number PROCESS_NUMBER
                            number of concurrent processes to spawn; WARNING: an
                            high number can trigger google serving limits!
                            (default: 4)

Here are some command examples
    
    gsuite_domain_checker -h
 This will show the help message
 
     gsuite_domain_checker -d google.com
 This will check the status of the domain google.com

    gsuite_domain_checker -cf domains.csv
 This will check the status of all the files in the domains.csv file (one domain per line)
 
     gsuite_domain_checker -cf domains.csv -td jhon.doe@mydomain.com
 This will check the status of all the files in the domains.csv file (one domain per line) and will write the output in a google spreadsheet shared with jhon.doe@mydomain.com
 
      gsuite_domain_checker -cf domains.csv -of domain_details.csv
 This will check the status of all the files in the domains.csv file (one domain per line) and will write the output in the domains_details.csv file

## Author
I am Lorenzo Persichetti and I work at [Revevol](https://www.revevol.com) helping customers in adopting cloud technologies.
I personally developed this tool to face complex G Suite deployments in which you need to provision many domains to a single console and you want to be aware if a domain is already part of another console.

I have used this tool many times and it proved to be a useful companion in the early stages of a G Suite deployment and that is why I am now sharing it as an open source tool.

This is also my first contribution to the open source community, so any feedback is absolutely welcome.