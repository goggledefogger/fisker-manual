import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fpdf import FPDF

def get_all_links(driver):
    # Get all links from the navigation menu
    nav_menu = driver.find_element(By.ID, "navigation_bar")
    links = nav_menu.find_elements(By.CSS_SELECTOR, "a.topiclink")
    return [link.get_attribute('href') for link in links]

def get_content(driver, url):
    driver.get(url)
    # Wait for the content to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "referenced_content"))
    )
    # Get the loaded content
    content = driver.find_element(By.ID, "referenced_content").get_attribute('innerHTML')
    return content

def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def create_pdf(contents):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for title, content in contents:
        pdf.cell(200, 10, txt=title, ln=1, align='C')
        pdf.multi_cell(0, 10, txt=content)
        pdf.add_page()

    pdf.output("owners_manual.pdf")

def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Use webdriver_manager to handle ChromeDriver installation
    service = ChromeService(ChromeDriverManager().install())

    # Initialize the webdriver with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html")  # Replace with the actual URL

        links = get_all_links(driver)
        contents = []

        for link in links:
            content_html = get_content(driver, link)
            title = driver.title
            content_text = html_to_text(content_html)
            contents.append((title, content_text))
            time.sleep(2)  # Add a small delay between requests

        create_pdf(contents)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
