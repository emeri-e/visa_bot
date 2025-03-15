import logging
import os
import random
import time
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.common.by import By
import urllib3

from utils.exceptions import LoginRedirectException, VisaTypeVerificationRedirectException, BadGatewayException, ForbiddenException, ProxyConnectionException



log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'requests.log')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class CustomSession(requests.Session):
    def __init__(self, max_retries=100, retry_wait=1):
        super().__init__()
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.timeout = 30
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.mount("http://", requests.adapters.HTTPAdapter())
    #     self.mount("https://", requests.adapters.HTTPAdapter())

    def refresh_connection(self):
        """Reset the connection to force IP rotation."""
        self.close()
        self.mount("http://", requests.adapters.HTTPAdapter())
        self.mount("https://", requests.adapters.HTTPAdapter())
        print("Connection refreshed to trigger IP rotation.")

    def request(self, method, url, caller, **kwargs):
        # ip_request = super().request('GET', 'https://api.ipify.org')
        logger.info(f"Requesting: {method} {url}")
        try:
            start_time = time.time()
            
            response = super().request(method, url,timeout=self.timeout, **kwargs)
            time_taken = time.time() - start_time
            logger.info(f"Response received: {response.status_code} in {time_taken:.2f} seconds")
            # Handle response history and redirects
            if response.history:
                last_response = response.history[-1]
                if last_response.status_code == 302:
                    if "login" in response.url.lower():
                        raise LoginRedirectException(f"Redirected to login page: {response.url}")
                    elif "visatypeverification" in response.url.lower():
                        raise VisaTypeVerificationRedirectException(f"Redirected to Visa Type Verification page: {response.url}")
            
            if response.status_code == 502:
                print("Bad Gateway (502) encountered. Retrying...")
                logger.error("Bad Gateway (502) encountered. Retrying...")
                for attempt in range(self.max_retries):
                    time.sleep(self.retry_wait)
                    response = super().request(method, url, **kwargs)
                    if response.status_code != 502:
                        break
                else:
                    raise BadGatewayException("Bad Gateway (502) after retries.")
            if response.status_code == 504:
                logger.error("Gateway timeout (504) encountered. Retrying...")
                for attempt in range(self.max_retries):
                    time.sleep(self.retry_wait)
                    response = super().request(method, url, **kwargs)
                    if response.status_code != 504:
                        break
                else:
                    raise BadGatewayException("Bad Gateway (502) after retries.")
            
            if response.status_code == 401:
                # print("Authorization error (401) encountered. Retrying...")
                raise LoginRedirectException(f"Redirected to login page: {response.url}")
            
            if response.status_code == 403:
                logger.error("Forbidden (403) encountered")
                if caller == "availability":
                    # print("Logining in afresh...")
                    raise LoginRedirectException("Logining in afresh")
                
                start_time = time.time()
                for attempt in range(10):
                    # logger.info(f"{attempt + 1}..")
                    time.sleep(self.retry_wait)
                    response = super().request(method, url, **kwargs)
                    if response.status_code != 403:
                        time_taken = time.time() - start_time
                        logger.info(f"403 fixed in: {response.status_code} in {time_taken:.2f} seconds")
                        # print("\n")
                        break

                else:
                    # print("\n")
                    time_taken = time.time() - start_time
                    logger.info(f"403 not fixed in {time_taken:.2f} seconds. redirecting...")
                    raise LoginRedirectException("Logining in afresh")
                    raise ForbiddenException("Forbidden (403) after retries.")

            return response

        #timeout error
        except requests.exceptions.ReadTimeout:
            logger.error("Timeout error. Retrying...")
            return self.request(method, url, caller, **kwargs)
            # for attempt in range(self.max_retries):
            #         time.sleep(self.retry_wait)
            #         return self.request(method, url, caller, **kwargs)
            # else:
            #     raise Exception("Timeout error persisted for too long")
        except requests.exceptions.ProxyError:
            logger.error("Proxy connection failed. Retrying...")
            for attempt in range(self.max_retries):
                    time.sleep(self.retry_wait)
                    return self.request(method, url, caller, **kwargs)
                    # response = super().request(method, url, **kwargs)
                    # if response.status_code != 502:
                    #     break
            else:
                raise ProxyConnectionException("Proxy connection failed.")
        
        except requests.exceptions.SSLError:
            logger.error("SSL error. Retrying...")
            for attempt in range(self.max_retries):
                    time.sleep(self.retry_wait)
                    return self.request(method, url, caller, **kwargs)
                    # response = super().request(method, url, **kwargs)
                    # if response.status_code != 502:
                    #     break
            else:
                raise Exception("SSL error persisted for too long")
        
        except urllib3.exceptions.SSLError:
            logger.error("urllib3 SSL error. Retrying...")
            for attempt in range(self.max_retries):
                    time.sleep(self.retry_wait)
                    return self.request(method, url, caller, **kwargs)
                    
            else:
                raise Exception("SSL error persisted for too long")
        
        except requests.exceptions.RequestException as e:
            # raise e
            logger.error(f" General Request error: {e}")
            return self.request(method, url, caller, **kwargs)

 
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get(self, url, caller=None, **kwargs):
        return self.request("GET", url, caller, **kwargs)

    def post(self, url, caller=None, **kwargs):
        return self.request("POST", url,caller, **kwargs)
    
class Browser:
    """Main class of the Pinterest uploader."""

    def __init__(self, proxy= None) -> None:
        """Set path of used file and start webdriver."""
        self._proxy = proxy
        self.driver = self.webdriver()

    def webdriver(self):
        """Start webdriver and return state of it."""
        options = webdriver.ChromeOptions()

        # spoofing options
        # x = self.get_desktop_user_agent()
        # print(x)
        # options.add_argument(f"user-agent={x}")
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

        options.add_argument('--disable-webgl')
        options.add_argument('--disable-canvas-fingerprint')

        options.add_argument("--disable-blink-features=AutomationControlled") 
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        
        options.add_experimental_option("useAutomationExtension", False) 
        
        if self._proxy:
            proxy_host = self._proxy['host']
            proxy_port = self._proxy['port']
            proxy_username = self._proxy['username']
            proxy_password = self._proxy['password']

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (proxy_host, proxy_port, proxy_username, proxy_password)
            pluginfile = 'proxy_auth_plugin.zip'

            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            options.add_extension(pluginfile)

        options.add_argument('--lang=en') 
        options.add_argument('log-level=3')
        options.add_argument('--mute-audio') 
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        
        
        return driver
            
    def get(self, url, max_retries=3):
        for attempt in range(max_retries):
            self.driver.get(url)
            self.driver.implicitly_wait(10)

            current_url = self.driver.current_url
            if url == current_url:
                break
            
        

    def clickable(self, element: str,by = By.XPATH) -> None:
        """Click on element if it's clickable using Selenium."""
        try:
            WDW(self.driver, 7).until(EC.element_to_be_clickable(
                (by, element))).click()
        except:
            self.driver.find_element(by, element).click()

    def visible(self, element: str, by = By.XPATH):
        """Check if element is visible using Selenium."""
        return WDW(self.driver, 15).until(EC.visibility_of_element_located(
            (by, element)))

    def send_keys(self, element: str, keys: str, by=By.XPATH, once=True) -> None:
        """Send keys to element if it's visible using Selenium."""
        try:
            elem = self.visible(element, by)

            if once:
                elem.send_keys(keys)
            else:
                for char in keys:
                    elem.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2)) 
        except Exception:
            self.driver.execute_script(f'arguments[0].innerText = "{keys}"', self.visible(element))

    def window_handles(self, window_number: int) -> None:
        """Check for window handles and wait until a specific tab is opened."""
        WDW(self.driver, 30).until(lambda _: len(
            self.driver.window_handles) == window_number + 1)

        self.driver.switch_to.window(self.driver.window_handles[window_number])


    