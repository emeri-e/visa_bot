from pages.details_page import DetailsPage
from pages.form_page import FormPage
from pages.intermediate_page import IntermediatePage
from pages.payment_page import PaymentPage
from .login_page import LoginPage
from .availability_page import AvailabilityPage


page_index = {
    'start': LoginPage,
    'intermediate': IntermediatePage,
    'availability_page': AvailabilityPage,
    'details_page': DetailsPage,
    'form_page': FormPage,
    'payment_page': PaymentPage
}

start_page = page_index['start']()
