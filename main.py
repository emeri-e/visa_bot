#!/usr/bin/env python3

from datetime import datetime, timedelta
import json
import logging
import multiprocessing
import os

import requests
from ocr.functions import is_ocr_server_running, start_ocr_server, wait_for_server
from pages import page_index, start_page

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from utils.gmail import Gmail
from utils.exceptions import EndException, LoginRedirectException, VisaTypeVerificationRedirectException, BadGatewayException, ForbiddenException, ProxyConnectionException

# log_dir = os.path.dirname(os.path.abspath(__file__))
# log_file = os.path.join(log_dir, 'main.log')
# logger = logging.getLogger(__name__)
# handler = logging.FileHandler(log_file)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)
# logger.setLevel(logging.DEBUG)


DEFAULT_USERNAME = "mudassarq16@gmail.com"
DEFAULT_PASSWORD = "Stone@11212"
DEFAULT_LOCATION = "Quetta"
DEFAULT_VISA_TYPE = "National Visa"
DEFAULT_VISA_SUBTYPE = "Family Reunion"
DEFAULT_CATEGORY = "Normal"
DEFAULT_PICTURE = ""


# LOCATIONS = ["Faisalabad", "Quetta", "Karachi"]
# VISA_TYPES = ["National Visa", "Legalisation Visa", "Schengen Visa"]
# VISA_SUBTYPES = ["Family Reunion", "Work", "Study"]
# CATEGORIES = ["Normal", "Premium"]




def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Get default image
def get_default_image():
    for file in os.listdir('./'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            return os.path.abspath(file)
    return ""

def get_numbers():
    numbers = []
    try:
        with open('whatsapp.txt', 'r') as file:
            for line in file:
                phone, apikey = line.strip().split(',')
                if phone and apikey:
                    numbers.append(phone)
            
            return numbers
    except FileNotFoundError:
        print("No whatsapp.txt file found.")
    except Exception as e:
        return

# Update Visa Types based on Location
def update_visa_types(*args):
    location_name = location_var.get()
    location = next((loc for loc in data['locationData'] if loc["Name"] == location_name), None)
    if location:
        visa_type_options = [visa["Name"] for visa in data['visaIdData'] if visa["LocationId"] == location["Id"]]
        visa_type_var.set("")
        visa_type_dropdown['values'] = visa_type_options
    else:
        visa_type_var.set("")
        visa_type_dropdown['values'] = []

# Update Visa Subtypes based on Visa Type
def update_visa_subtypes(*args):
    visa_type_name = visa_type_var.get()
    visa_type = next((visa for visa in data['visaIdData'] if visa["Name"] == visa_type_name), None)
    if visa_type:
        visa_subtype_options = [sub["Name"] for sub in data['visasubIdData'] if sub["Value"] == visa_type["Id"]]
        visa_subtype_var.set("")
        visa_subtype_dropdown['values'] = visa_subtype_options
    else:
        visa_subtype_var.set("")
        visa_subtype_dropdown['values'] = []

# Update Categories based on Visa Subtype
def update_categories(*args):
    visa_subtype_name = visa_subtype_var.get()
    visa_subtype = next((sub for sub in data['visasubIdData'] if sub["Name"] == visa_subtype_name), None)
    if visa_subtype:
        category_options = [cat["Name"] for cat in data['AppointmentCategoryIdData']]
        category_var.set("")
        category_dropdown['values'] = category_options
    else:
        category_var.set("")
        category_dropdown['values'] = []

# Load JSON data
data = load_json('data.json')  # Update with your JSON file path
default_image = get_default_image()

def upload_passport():
    """
    Opens a file dialog for the user to select a passport file.
    """
    file_path = filedialog.askopenfilename(
        title="Select Passport File",
        filetypes=(("All Files", "*.*"),("PDF Files", "*.pdf"), ("Image Files", "*.jpg;*.jpeg;*.png"))
    )
    passport_var.set(file_path)  

def start_application():
    """
    Starts the main application after gathering user inputs.
    """
    username = username_var.get()
    password = password_var.get()
    location = location_var.get()
    visa_type = visa_type_var.get()
    visa_subtype = visa_subtype_var.get()
    category = category_var.get()
    passport_path = passport_var.get()
    use_proxy = use_proxy_var.get()
    local_ocr = use_local_ocr_var.get()

    firstname = firstname_var.get()
    lastname = lastname_var.get()
    surname = surname_var.get()
    pob = pob_var.get()
    gender = gender_var.get()
    marital_status = marital_status_var.get()
    nationality = nationality_var.get()
    nationality_birth = nationality_birth_var.get()
    country = country_var.get()
    inviting_authority_name = inviting_authority_name_var.get()

    whatsapp_number = whatsapp_number_var.get()
    whatsapp_apikey = whatsapp_apikey_var.get()
    error_message_var.set("")

    range_selection = range_var.get()
    # if range_selection == "Day":
    #     selected_date = selected_day_var.get()
    #     try:
    #         formatted_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    #     except ValueError:
    #         error_message_var.set("Invalid date. Please use YYYY-MM-DD.")
    #         return
    #         # raise Exception("Wrong date. Ensure it is in the format: YYYY-MM-DD")
    # else:
    #     formatted_date = range_selection

    selected_date = selected_day_var.get()
    try:
        formatted_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        error_message_var.set("Invalid date. Please use YYYY-MM-DD.")
        return


    # Close the GUI window
    root.destroy()
    
    # Pass these variables to the rest of your script (e.g., the context dictionary)
    context = {
        "username": username,
        "password": password,
        "location": location,
        "visatype": visa_type,
        "visasubtype": visa_subtype,
        "category": category,
        "image_file_path": passport_path,
        "use_proxy": use_proxy,
        "local_ocr": local_ocr,
        'gmail': Gmail(username),
        
        "whatsapp_number": whatsapp_number,
        "whatsapp_apikey": whatsapp_apikey,
        "date_selection": formatted_date,  
        "range_selection": range_selection,

        'FirstName' : firstname,
        'LastName' : lastname,
        'SurName' : surname,
        'PlaceOfBirth' : pob,
        'GenderId' : next((x['Id'] for x in data['genderData'] if x["Name"] == gender)),
        'MaritalStatusId' : next((x['Id'] for x in data['maritalStatusData'] if x["Name"] == marital_status)),
        'NationalityId' : next((x['Id'] for x in data['countryData'] if x["Name"] == nationality)),
        'NationalityAtBirthId' : next((x['Id'] for x in data['countryData'] if x["Name"] == nationality_birth)),
        'CountryOfBirthId' : next((x['Id'] for x in data['countryData'] if x["Name"] == country)),
        'InvitingAuthorityName' : inviting_authority_name

        
    }
    with open('saved_choices.json', 'w') as f:
        copy = context.copy()
        copy.pop('gmail', None)
        copy['gender'] = gender
        copy['marital_status'] = marital_status
        copy['nationality'] = nationality
        copy['nationality_birth'] = nationality_birth
        copy['country'] = country
        json.dump(copy, f)

    if not local_ocr:
        if not is_ocr_server_running():
            ocr_process = multiprocessing.Process(target=start_ocr_server)
            ocr_process.start()
            wait_for_server()
        
    main_process(context)

def main_process(context):
    # ip_request = requests.get('https://api.ipify.org')
    # print(f"IP Address: {ip_request.text}")

    page = start_page
    next_page = 'start'

    while True:
        try:
            if context.get('next_page'):
                next_page = context['next_page']
                del context['next_page']
            elif context.get('return_to_page'):
                next_page = context['return_to_page']
                del context['return_to_page']
            
            # if not next_page:
            #     break
            
            page = page_index[next_page]()

            # print('=' * 10, str(page), '=' * 10)
            ctx = page.process(context)
            context.update(ctx)
            next_page = page.next()
        
        except LoginRedirectException as e:
            print('\nRedirecting to login page...')
            context['next_page'] = 'start'
            context['return_to_page'] = next_page

        except VisaTypeVerificationRedirectException as e:
            print('\nRedirecting to Visa Type verification page...')
            context['next_page'] = 'availability_page'
            context['return_to_page'] = next_page
            
        except BadGatewayException as e:
            page.logger.error(f"Bad gateway persisted fo long: {e}")
        except ForbiddenException as e:
            page.logger.error(f"Forbidden access persisted for long: {e}")
        except ProxyConnectionException as e:
            page.logger.error(f"Proxy error: {e}")
        except EndException as e:
            page.logger.error(f"Script ended: {e}")
            # print("Successfully reached the end.")
            break
        except requests.RequestException as e:
            page.logger.error(f"General request error: {e}", exc_info=True)
        except Exception as e:
            # print('Redirecting to login page...')
            # context['next_page'] = 'start'
            page.logger.error(f"Unknown error: {e}", exc_info=True)

root = tk.Tk()
root.title("Visa Application Form")

try:
    with open('saved_choices.json', 'r') as f:
        saved_choices = json.load(f)
except FileNotFoundError:
    saved_choices = {}

username_var = tk.StringVar(value=saved_choices.get('username', DEFAULT_USERNAME))
password_var = tk.StringVar(value=saved_choices.get('password', DEFAULT_PASSWORD))
email_password_var = tk.StringVar(value=saved_choices.get('email_password', ''))
location_var = tk.StringVar(value=saved_choices.get('location', ''))
visa_type_var = tk.StringVar(value=saved_choices.get('visatype', ''))
visa_subtype_var = tk.StringVar(value=saved_choices.get('visasubtype', ''))
category_var = tk.StringVar(value=saved_choices.get('category', ''))

_path = saved_choices.get('image_file_path')
if os.path.exists(_path):
    default_image = _path
passport_var = tk.StringVar(value=default_image)

use_proxy_var = tk.BooleanVar(value=saved_choices.get('use_proxy', True))
use_local_ocr_var = tk.BooleanVar(value=saved_choices.get('local_ocr', False)) 

nationality_var = tk.StringVar(value=saved_choices.get('nationality', 'Pakistan'))
nationality_birth_var = tk.StringVar(value=saved_choices.get('nationality_birth', 'Pakistan'))
country_var = tk.StringVar(value=saved_choices.get('country', 'Pakistan'))
gender_var = tk.StringVar(value=saved_choices.get('gender', 'Male'))
marital_status_var = tk.StringVar(value=saved_choices.get('marital_status', 'Single'))

firstname_var = tk.StringVar(value=saved_choices.get('FirstName', 'MUDASSAR'))
lastname_var = tk.StringVar(value=saved_choices.get('LastName', 'QURESHI'))
surname_var = tk.StringVar(value=saved_choices.get('SurName', 'QURESHI'))
pob_var = tk.StringVar(value=saved_choices.get('PlaceOfBirth', 'Quetta'))
inviting_authority_name_var = tk.StringVar(value=saved_choices.get('InvitingAuthorityName', 'Italy'))

whatsapp_number_var = tk.StringVar(value=saved_choices.get('whatsapp_number', "923125082292"))
whatsapp_apikey_var = tk.StringVar(value=saved_choices.get('whatsapp_apikey', "8140513"))

range_var = tk.StringVar(value=saved_choices.get('range_selection', 'Day')) 
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
selected_day_var = tk.StringVar(value=saved_choices.get('date_selection', tomorrow))  

# Date selection
tk.Label(root, text="Select Range:").grid(row=12, column=0, sticky="e", padx=10, pady=5)
range_dropdown = ttk.Combobox(root, textvariable=range_var, values=["Day", "Week", "Month"], width=22, state="readonly")
range_dropdown.grid(row=12, column=1, pady=5)

day_label = tk.Label(root, text="Till Day:")
day_label.grid(row=12, column=2, sticky="e", padx=10, pady=5)
# day_label.grid_remove() 

start_day_label = tk.Label(root, text="Start Day:")
start_day_label.grid(row=12, column=2, sticky="e", padx=10, pady=5)
start_day_label.grid_remove() 

day_entry = tk.Entry(root, textvariable=selected_day_var, width=15)
day_entry.grid(row=12, column=3, pady=5)
# day_entry.grid_remove() 

def update_day_selector(*args):
    if range_var.get() == "Day":
        day_label.grid()
        start_day_label.grid_remove()
        # day_entry.grid()
    else:
        day_label.grid_remove()
        start_day_label.grid()
        # day_entry.grid_remove()

range_var.trace_add('write', update_day_selector)
# Date selection end

error_message_var = tk.StringVar(value="")  # Empty string means no error
error_label = tk.Label(root, textvariable=error_message_var, fg="red")
error_label.grid(row=10, column=1, columnspan=2, pady=5)

# Bind dynamic updates
location_var.trace_add('write', update_visa_types)
visa_type_var.trace_add('write', update_visa_subtypes)
visa_subtype_var.trace_add('write', update_categories)

tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=username_var, width=25).grid(row=0, column=1, pady=5)

tk.Label(root, text="Password:").grid(row=0, column=2, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=password_var, show="*", width=25).grid(row=0, column=3, pady=5)

tk.Label(root, text="Location:").grid(row=2, column=0, sticky="e", padx=10, pady=5)
location_dropdown = ttk.Combobox(root, textvariable=location_var, values=[loc["Name"] for loc in data['locationData']], width=22, state="readonly")
location_dropdown.grid(row=2, column=1, pady=5)

tk.Label(root, text="Visa Type:").grid(row=2, column=2, sticky="e", padx=10, pady=5)
visa_type_dropdown = ttk.Combobox(root, textvariable=visa_type_var, values=[], width=22, state="readonly")
visa_type_dropdown.grid(row=2, column=3, pady=5)

tk.Label(root, text="Visa Subtype:").grid(row=4, column=0, sticky="e", padx=10, pady=5)
visa_subtype_dropdown = ttk.Combobox(root, textvariable=visa_subtype_var, values=[], width=22, state="readonly")
visa_subtype_dropdown.grid(row=4, column=1, pady=5)

tk.Label(root, text="Category:").grid(row=4, column=2, sticky="e", padx=10, pady=5)
category_dropdown = ttk.Combobox(root, textvariable=category_var, values=[], width=22, state="readonly")
category_dropdown.grid(row=4, column=3, pady=5)

tk.Label(root, text="Picture:").grid(row=6, column=0, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=passport_var, width=40, state="readonly").grid(row=6, column=1, pady=5)
tk.Button(root, text="Select", command=upload_passport).grid(row=6, column=2, padx=5)

tk.Label(root, text="Use Proxy:").grid(row=7, column=0, sticky="e", padx=10, pady=5)
tk.Radiobutton(root, text="Yes", variable=use_proxy_var, value=True).grid(row=7, column=1, sticky="w")
tk.Radiobutton(root, text="No", variable=use_proxy_var, value=False).grid(row=7, column=2, sticky="w")

tk.Label(root, text="OCR type:").grid(row=8, column=0, sticky="e", padx=10, pady=5)
tk.Radiobutton(root, text="independent", variable=use_local_ocr_var, value=True).grid(row=8, column=1, sticky="w")
tk.Radiobutton(root, text="shared", variable=use_local_ocr_var, value=False).grid(row=8, column=2, sticky="w")

tk.Label(root, text="Valid WhatsApp Numbers:").grid(row=9, column=0, sticky="e", padx=10, pady=5)
tk.Button(root, text=str(get_numbers())).grid(row=9, column=1, pady=0)
# c = 1
# for number in get_numbers():
#     tk.Button(root, text=number, width=4).grid(row=9, column=c, pady=0)
#     c += 1
# tk.Entry(root, textvariable=whatsapp_number_var, width=25).grid(row=9, column=1, pady=5)

# tk.Label(root, text="WhatsApp API Key:").grid(row=9, column=2, sticky="e", padx=10, pady=5)
# tk.Entry(root, textvariable=whatsapp_apikey_var, show="*", width=25).grid(row=9, column=3, pady=5)
        
# tk.Label(root, text="Email password:").grid(row=10, column=0, sticky="e", padx=10, pady=5)
# tk.Entry(root, textvariable=email_password_var, show="*", width=25).grid(row=10, column=1, pady=5)

tk.Label(root, text="Application Details").grid(row=11, column=1, sticky="e", padx=10, pady=20)

tk.Label(root, text="First name:").grid(row=25, column=0, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=firstname_var, width=25).grid(row=25, column=1, pady=5)

tk.Label(root, text="Last name:").grid(row=25, column=2, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=lastname_var, width=25).grid(row=25, column=3, pady=5)

tk.Label(root, text="Surname:").grid(row=27, column=0, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=surname_var, width=25).grid(row=27, column=1, pady=5)

tk.Label(root, text="Place of Birth:").grid(row=27, column=2, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=pob_var, width=25).grid(row=27, column=3, pady=5)

# tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
# tk.Entry(root, textvariable=username_var, width=25).grid(row=0, column=1, pady=5)

tk.Label(root, text="Nationality:").grid(row=13, column=0, sticky="e", padx=10, pady=5)
country_dropdown = ttk.Combobox(root, textvariable=nationality_var, values=[loc["Name"] for loc in data['countryData']], width=22, state="readonly")
country_dropdown.grid(row=13, column=1, pady=5)

tk.Label(root, text="Nationality at Birth:").grid(row=13, column=2, sticky="e", padx=10, pady=5)
location_dropdown = ttk.Combobox(root, textvariable=nationality_birth_var, values=[loc["Name"] for loc in data['countryData']], width=22, state="readonly")
location_dropdown.grid(row=13, column=3, pady=5)

tk.Label(root, text="Country of Birth:").grid(row=15, column=0, sticky="e", padx=10, pady=5)
location_dropdown = ttk.Combobox(root, textvariable=country_var, values=[loc["Name"] for loc in data['countryData']], width=22, state="readonly")
location_dropdown.grid(row=15, column=1, pady=5)

tk.Label(root, text="Gender:").grid(row=20, column=0, sticky="e", padx=10, pady=5)
location_dropdown = ttk.Combobox(root, textvariable=gender_var, values=[loc["Name"] for loc in data['genderData']], width=22, state="readonly")
location_dropdown.grid(row=20, column=1, pady=5)


tk.Label(root, text="Inviting Authority Name:").grid(row=30, column=0, sticky="e", padx=10, pady=5)
tk.Entry(root, textvariable=inviting_authority_name_var, width=25).grid(row=30, column=1, pady=5)

tk.Label(root, text="Marital Status:").grid(row=20, column=2, sticky="e", padx=10, pady=5)
location_dropdown = ttk.Combobox(root, textvariable=marital_status_var, values=[loc["Name"] for loc in data['maritalStatusData']], width=22, state="readonly")
location_dropdown.grid(row=20, column=3, pady=5)

tk.Button(root, text="Start bot", command=start_application).grid(row=50, column=0, columnspan=3, pady=20)

root.mainloop()
