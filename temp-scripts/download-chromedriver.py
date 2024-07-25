import requests
from bs4 import BeautifulSoup
import pdfkit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to your chromedriver
chromedriver_path = '/opt/homebrew/bin/chromedriver'  # Update this path

# Set up Selenium with specific options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--remote-debugging-port=9222')

service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

# Fetch the main page
url = 'https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html'
driver.get(url)

# Wait for the page to load and ensure all sections are expanded
wait = WebDriverWait(driver, 10)
expand_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button')))  # Update selector accordingly

for button in expand_buttons:
    driver.execute_script("arguments[0].click();", button)

# Extract the fully rendered HTML content
html_content = driver.page_source

# Save the concatenated HTML to a temporary file
html_file_path = 'full_content.html'
with open(html_file_path, 'w') as file:
    file.write(html_content)

# Convert the HTML file to PDF using pdfkit
pdf_file_path = 'Fisker_Ocean_Owners_Manual.pdf'
pdfkit.from_file(html_file_path, pdf_file_path)

# Clean up
driver.quit()

print(f"PDF generated successfully at {pdf_file_path}")
