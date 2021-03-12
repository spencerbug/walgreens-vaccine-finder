from chromedriver_py import binary_path  # this will get you the path variable
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from datetime import date
from twilio.rest import Client
from time import sleep
from random import randint
import json


def random_sleep(low, high):
    tts=randint(low, high)
    for i in range(tts):
        sleep(1)
        print(f"{tts-i}..", end="\r")


fp = open("config.json")
config = json.load(fp)
fp.close()

def get_option(obj):
    for item in obj:
        for k,v in item.items():
            if v==True:
                return k
    return "No option selected"


def fill_filled_textbox(elem, text):
    elem.send_keys(Keys.CONTROL + Keys.COMMAND + 'a')
    elem.send_keys(Keys.DELETE)
    elem.send_keys(text)

class SMSClient:
    def __init__(self):
        self.config_sms=config['NOTIFICATIONS']['text_message']
        self.client=None
    
    def activate(self):
        if self.is_enabled():
            self.client = Client(self.config_sms['twilio_sid'], self.config_sms['twilio_token'])
            # notify you will receive alerts
            # self.send("You will receive alerts from this number about walgreens covid vaccines.")
    def is_enabled(self):
        return self.config_sms['Enabled']
    def send(self, msg):
        if self.is_enabled():
            self.client.messages.create(body=msg,from_=self.config_sms['twilio_phone'],to=config['phone'])


driver = webdriver.Chrome(executable_path=binary_path)
driver.implicitly_wait(5)

#login attempt loop
while True:
    try:
        # Enter login credentials
        driver.get("https://www.walgreens.com/login.jsp")
        driver.find_element_by_id("user_name").send_keys(config['walgreens_username'])
        driver.find_element_by_id("user_password").send_keys(config['walgreens_password'])
        driver.find_element_by_id("submit_btn").click()
        sleep(3)
        # check if security page:
        if "verify_identity" in driver.current_url:
            #choose to verify via security question
            driver.find_element_by_id("radio-security").click()
            driver.find_element_by_id("optionContinue").click()
            driver.find_element_by_id("secQues").send_keys(config['walgreens_security_question_answer'])
            driver.find_element_by_id("validate_security_answer").click()
            wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//h1[text()="Your Account"]')))
        wait(driver, 5).until(EC.presence_of_element_located((By.XPATH,"//*[text()='Your Account']")))
        break
    except:
        print("Unable to login. Closing and reopening...")
        driver.close()
        random_sleep(10,90)
        driver = webdriver.Chrome(executable_path=binary_path)
        continue

landing_page="https://www.walgreens.com/findcare/vaccination/covid-19?ban=covid_vaccine_landing_schedule"

smsclient = SMSClient()
smsclient.activate()

search_miniloop=True

while True:
    try:
        driver.get(landing_page)
        driver.get("https://www.walgreens.com/findcare/vaccination/covid-19/location-screening")
        sleep(1)

        # page 1: Search pharmacies based on address
        wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="inputLocation"]')))
        sleep(1) #wait for textbox to be filled in
        fill_filled_textbox(driver.find_element_by_id("inputLocation"), config['address'])

        # run in a mini loop here just clicking search
        while True:
            driver.find_element_by_xpath("//*[text()='Search']").click()
            # check if appointments available
            apt_availability_status_xpath = "//*[contains(text(),'Appointments')]"
            status = wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, apt_availability_status_xpath)))
            if "available!" in status.text.lower():
                break
            else:
                print(f"{datetime.now()}::No appointments available, retrying...")
                random_sleep(1,10)
                continue
        
        # Send an alert if we got something!
        smsclient.send(f"Walgreens Cov19 vaccine appointments avilable in your area! {landing_page}")

        # page 3: legal elligibility
        driver.find_element_by_xpath("//*[contains(text(),'See if you’re eligible')]").click()
        wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Complete the form below to continue.']")))
        statement_that_describes_you = get_option(config['SELECT_ONLY_ONE_statement_that_describes_you'])
        
        driver.find_element_by_xpath(f"//*[@aria-label='{statement_that_describes_you}']/../..").click()
        driver.find_element_by_id('eligibility-check').click()
        driver.find_element_by_xpath("//input[@value='Continue']").click()
        # page 4: health screening
        wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[text()='COVID-19 Vaccination Screening']")))
        if config['do_you_have_authorization_code']:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'authorization code')]/../div[1]/label").click()
            driver.find_element_by_xpath('//*[@id="sq_101i"]').send_keys(config['authorization_code'])
        else:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'authorization code')]/../div[2]/label").click()
        
        if config['do_you_have_covid_symptoms']:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'fever')]/../div[1]/label").click()
        else:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'fever')]/../div[2]/label").click()

        if config['have_you_tested_positive_for_cov19_in_past_2_weeks']:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'tested positive')]/../div[1]/label").click()
        else:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'tested positive')]/../div[2]/label").click()

        if config['do_you_have_chronic_health_condition']:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'chronic')]/../div[1]/label").click()
        else:
            driver.find_element_by_xpath("//*[contains(@aria-label, 'chronic')]/../div[2]/label").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()
        # page 5: Elligibility results and vaccination
        if len(driver.find_elements_by_xpath("//*[contains(text(),'you are eligible')]")) == 0:
            print("Sorry you are not eligible.")
            exit()
        # page 6: patient intake form
        driver.get("https://www.walgreens.com/findcare/vaccination/covid-19/appointment/patient-info")
        wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Schedule your vaccination']")))
        Select(driver.find_element_by_id("race-dropdown")).select_by_visible_text(get_option(config['SELECT_ONLY_ONE_race']))
        Select(driver.find_element_by_id("ethnicity-dropdown")).select_by_visible_text(get_option(config['SELECT_ONLY_ONE_ethnicity']))

        fill_filled_textbox(driver.find_element_by_id("field-phone"), config['phone'])

        driver.find_element_by_xpath(f"//*[text()='{get_option(config['SELECT_ONLY_ONE_which_dose'])}']/../..").click()

        driver.find_element_by_id("continueBtn").click()

        

        if len(driver.find_elements_by_xpath("//*[contains(@class, 'icon__alert')]")) > 0:
            print("Got error")
            sleep(5)
            continue
        
        #want to continue here but can't since I haven't gotten this far yet
        print("Continue here!!")
        
    except:
        random_sleep()
        continue






    




