from decouple import config

class BaseConfig:
    login_url = 'https://ita-pak.blsinternational.com/Global/Account/LogIn'
    captcha_submit_url = 'https://ita-pak.blsinternational.com/Global/CaptchaPublic/SubmitCaptcha'

    # proxy config
    proxy_user = config('PROXY_USER')
    proxy_password = config('PROXY_PASSWORD')
    proxy_ip = config('PROXY_IP')
    proxy_port = config('PROXY_PORT')
    proxy = f'{proxy_user}:{proxy_password}@{proxy_ip}:{proxy_port}'

    # true captcha data
    tcaptcha_url = 'https://api.apitruecaptcha.org/one/gettext'   
    tcaptcha_username = config('TCAPTCHA_USERNAME')
    tcaptcha_apikey = config('TCAPTCHA_APIKEY')

     

base = BaseConfig()