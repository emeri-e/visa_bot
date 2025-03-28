import os
from decouple import config

class BaseConfig:
    login_url = 'https://ita-pak.blsinternational.com/Global/Account/LogIn'
    captcha_submit_url = 'https://ita-pak.blsinternational.com/Global/CaptchaPublic/SubmitCaptcha'

    # proxy config("http://spoah8u2pq:gkeF46R1z=R3vVummx@pk.smartproxy.com:10001")
    # 'http://{}:{}@as.qy58xuwl.lunaproxy.net:12233'.format("user-aJsonu_G5gzD-region-pk", "Aliabbasi123")
    
    # proxy_user = config('PROXY_USER', default='spoah8u2pq')
    # proxy_password = config('PROXY_PASSWORD', default='gkeF46R1z=R3vVummx')
    # proxy_ip = config('PROXY_IP', default='pk.smartproxy.com')
    # proxy_port = config('PROXY_PORT', default='10001')
    
    proxy_user = config('PROXY_USER')
    proxy_password = config('PROXY_PASSWORD')
    proxy_ip = config('PROXY_IP')
    proxy_port = config('PROXY_PORT')
    
    proxy = f'http://{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}'

    # true captcha data
    tcaptcha_url = 'https://api.apitruecaptcha.org/one/gettext'
    tcaptcha_username = config('TCAPTCHA_USERNAME')
    tcaptcha_apikey = config('TCAPTCHA_APIKEY')


     
base = BaseConfig()
