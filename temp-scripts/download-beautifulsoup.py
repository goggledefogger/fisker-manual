import requests
from bs4 import BeautifulSoup
from weasyprint import HTML

# Fetch the main page content
url = 'https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all section links within the main content
base_url = 'https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/'
links = [base_url + a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('content')]

# Include the main page in the links to be converted
pdf_links = [url] + links

# Fetch and concatenate the HTML content from each link
full_html_content = ''
for link in pdf_links:
    page_response = requests.get(link)
    page_soup = BeautifulSoup(page_response.content, 'html.parser')
    full_html_content += str(page_soup)

# Save the concatenated HTML to a temporary file
html_file_path = 'full_content.html'
with open(html_file_path, 'w') as file:
    file.write(full_html_content)

# Convert the HTML file to PDF using weasyprint
pdf_file_path = 'Fisker_Ocean_Owners_Manual.pdf'
HTML(html_file_path).write_pdf(pdf_file_path)

print(f"PDF generated successfully at {pdf_file_path}")
