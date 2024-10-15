from decouple import config

class BaseConfig:
    login_url = 'https://ita-pak.blsinternational.com/Global/Account/LogIn'
    captcha_submit_url = 'https://ita-pak.blsinternational.com/Global/CaptchaPublic/SubmitCaptcha'

    # proxy config("http://spoah8u2pq:gkeF46R1z=R3vVummx@pk.smartproxy.com:10001")
    proxy_user = config('PROXY_USER', default='spckd77hx3')
    proxy_password = config('PROXY_PASSWORD', default='C3EP8mm+sd92qHhnhw')
    proxy_ip = config('PROXY_IP', default='pk.smartproxy.com')
    proxy_port = config('PROXY_PORT', default='10001')
    
    proxy = f'http://{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}'

    # true captcha data
    tcaptcha_url = 'https://api.apitruecaptcha.org/one/gettext'   
    tcaptcha_username = config('TCAPTCHA_USERNAME')
    tcaptcha_apikey = config('TCAPTCHA_APIKEY')

     
base = BaseConfig()
