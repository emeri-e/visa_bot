import random
import time

from bs4 import BeautifulSoup
import requests

from utils.exceptions import EndException
from utils.functions import create_session, extract_applicant
from utils.models import Browser
from .base import Page
from utils.functions import extract_json
from requests_toolbelt.multipart.encoder import MultipartEncoder
import urllib.parse

import json
import re


class PaymentPage(Page):
    def __str__(self):
        return 'Payment'

    def get_valid_fields(self, page_text):
        soup = BeautifulSoup(page_text, 'html.parser')
        result = {}

        # Extract inputs and populate `result`
        for input_field in soup.find_all('input'):
            name = input_field.get('name')
            id = input_field.get('id')

            value = input_field.get('value', '')
            if name and value:
                result[name] = value
            elif id and value:
                if 'data-service-id' in input_field.attrs:
                    service_id = input_field['data-service-id']
                    service_value = value
                    if service_value:
                        result['ValueAddedServices'] = f"{service_id}_{service_value}"
                else:
                    id = id.split('_')[0]
                    result[id] = value

        return result

    def process(self, context):
        session = context['session']
        # url = context['returnUrl']  # The URL for the payment page
        url = f"https://ita-pak.blsinternational.com/Global/BlsAppointment/VisaAppointmentPaymentForm?appointmentId={context['appointment_id']}"
        # Fetch the payment page
        response = session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch the payment page: {response.status_code}")

        # Extract valid fields
        self.valid_fields = self.get_valid_fields(response.text)

        # Prepare the payload
        payload = self.valid_fields
        # {
        #     'Id': self.valid_fields.get('Id'),
        #     'ValueAddedServices': self.valid_fields.get('ValueAddedServices', ''),
        # }

        # Send the payment request
        payment_request_url = "https://ita-pak.blsinternational.com/Global/payment/PaymentRequest"
        headers = {
            'RequestVerificationToken': context['appointment_rvt'],
        }

        print("Sending payment request...")
        payment_response = session.post(payment_request_url, data=payload, headers=headers)
        if payment_response.status_code != 200:
            raise Exception(f"Failed to send payment request: {payment_response.status_code}")

        # Extract the payment URL from the response and save it
        payment_data = payment_response.json()
        payment_url = payment_data.get('requestURL')
        if not payment_url:
            raise Exception("Payment URL not found in the response.")

        # Save the payment URL to a file
        with open(f'payment_url_{context["FirstName"]}.txt', 'w') as file:
            file.write(payment_url)

        # phone = context['whatsapp_number']
        # apikey = context['whatsapp_apikey']
        # message = f"""Name: {context['FirstName']} {context['LastName']}\nCenter: {context['location']}\nPayment URL: {payment_url}"""
        # url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={urllib.parse.quote(message)}&apikey={apikey}" # f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={message}&apikey={apikey}"
        # r = requests.get(url)
        
        try:
            with open('whatsapp.txt', 'r') as file:
                for line in file:
                    phone, apikey = line.strip().split(',')
                    message = f"""Name: {context['FirstName']} {context['LastName']}\nCenter: {context['location']}\nPayment URL: {payment_url}"""
                    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={urllib.parse.quote(message)}&apikey={apikey}"
                    r = requests.get(url)
        except FileNotFoundError:
            print("No whatsapp.txt file found.")
        except Exception as e:
            print(f"Failed to send all whatsapp message: {e}")

        # with open('whatsapp.html', 'w') as f:
        #     f.write(r.text)
        # https://console.cloud.google.com/apis/credentials/consent?authuser=2&project=pinterest-1952

        print(f"Payment URL saved: {payment_url}")

        raise EndException('Script completed successfully')