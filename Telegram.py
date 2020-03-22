
import time
import selenium.webdriver as webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


class Telegram:
    def __init__(self, tel_nr):
        print('Setting up Telegram page.\nDO NOT close the browser window or you wont get any more messages.\n')

        # start browser
        self.driver = webdriver.Firefox()
        # driver.minimize_window()
        self.driver.get('https://web.telegram.org/#/im')  # go to telegram web

        # enter phone number
        linkElem = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[2]/input')))
        time.sleep(2)
        linkElem.send_keys(tel_nr, Keys.RETURN)

        # confirm phone number
        linkElem = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[4]/div[2]/div/div/div[2]/button[2]/span')))
        linkElem.click()
        time.sleep(2)
        # enter the security code
        code_box = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@name='phone_code']")))
        code = input('Enter the code from your SMS here: ')
        # confirm login with code
        try:
            code_box.send_keys(code, Keys.RETURN)
        except:
            pass

        # wait for chats to load
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
            (By.CLASS_NAME, 'im_dialog_peer')))

        # get a list of all chats
        chat_list = self.driver.find_elements_by_class_name(
            'im_dialog_peer')

        for chat in chat_list:
            if (chat.text == 'Gespeichertes'):
                reporting_chat = chat
                print(f'Reports to {reporting_chat}.')
                break

        reporting_chat.click()
        self.driver.minimize_window()

    def report(self, txt):
        # enter txt and send
        text_field = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[1]/div[2]/div/div[2]/div[3]/div/div[3]/div[2]/div/div/div/form/div[2]/div[5]")))  # get text field
        text_field.send_keys(txt, Keys.RETURN)
