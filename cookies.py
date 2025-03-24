import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By  # <-- Added import
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pickle
from getpass import getpass

# Your email and password (replace these with your actual Gmail credentials)
email = input("Enter your email id: ")
password = getpass("Enter your password: ")

# Launch Chrome using webdriver_manager
options = webdriver.ChromeOptions()
browser = uc.Chrome(executable_path=ChromeDriverManager().install(), options=options)

# Open Gmail login page
browser.get("https://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1&hl=en&flowName=GlifWebSignIn&flowEntry=ServiceLogin")


# Enter email and click 'Next'
browser.find_element(By.ID, 'identifierId').send_keys(email)
browser.find_element(By.CSS_SELECTOR, '#identifierNext > div > button > span').click()

# Wait for the password field to appear
password_selector = "#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input"
WebDriverWait(browser, 10).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))

# Enter the password and click 'Next'
browser.find_element(By.CSS_SELECTOR, password_selector).send_keys(password)
browser.find_element(By.CSS_SELECTOR, '#passwordNext > div > button > span').click()

# Wait for Gmail to load
time.sleep(5)

# Get the cookies after login
cookies = browser.get_cookies()

# Save the cookies to a file
with open("cookies.pkl", "wb") as cookie_file:
    pickle.dump(cookies, cookie_file)

print("✅ Cookies downloaded successfully!")
