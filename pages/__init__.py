from .login_page import LoginPage
from .availability_page import AvailabilityPage


page_index = {
    'start': LoginPage,
    'availability_page': AvailabilityPage,
}

start_page = page_index['start']()
