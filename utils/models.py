import random
import time
import zipfile
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.common.by import By

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
            proxy_host = self._proxy.host
            proxy_port = self._proxy.port
            proxy_username = self._proxy.username
            proxy_password = self._proxy.password

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
            if url.split('/')[3] in current_url:
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


    