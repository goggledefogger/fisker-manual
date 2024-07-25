import asyncio
from playwright.async_api import async_playwright
import hashlib
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Debug flag and section limit
DEBUG = True
DEBUG_SECTION_LIMIT = 5

def get_content_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

async def get_content(page):
    await page.wait_for_selector("#ohb_topic")

    content = await page.evaluate("""
        () => {
            const obj = document.querySelector('#ohb_topic');
            if (obj && obj.contentDocument) {
                const body = obj.contentDocument.body;
                // Debug: Log the HTML structure
                console.log('HTML structure:', body.innerHTML);

                // Exclude the header elements
                const headerElements = body.querySelectorAll('h1, h2, h3, h4, h5, h6');
                headerElements.forEach(el => el.remove());

                // Get the remaining text content
                return body.innerText;
            }
            return '';
        }
    """)

    return content

async def scrape_website(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url)
        await page.wait_for_selector("#navigation_bar")

        nav_items = await page.query_selector_all("#navigation_bar li")

        contents = []
        processed_content_hashes = set()
        processed_count = 0

        for index, item in enumerate(nav_items):
            try:
                section_title = await item.inner_text()
                level = len(await item.query_selector_all("xpath=ancestor::ul"))

                await item.click()
                await asyncio.sleep(2)  # Wait for content to load

                content = await get_content(page)
                content_hash = get_content_hash(content)

                print(f"Processing: {section_title}")
                print(f"Content hash: {content_hash}")
                print("Content preview: {}...".format(content[:100].replace('\n', ' ')))

                if content_hash in processed_content_hashes:
                    print(f"Skipping duplicate content: {section_title}")
                    continue

                contents.append((level, section_title, content))
                processed_content_hashes.add(content_hash)
                processed_count += 1
                print(f"Processed [{processed_count}/{len(nav_items)}]: {section_title} (Level {level})")

                if DEBUG and processed_count >= DEBUG_SECTION_LIMIT:
                    print(f"Debug mode: Stopped after processing {processed_count} sections")
                    break

            except Exception as e:
                print(f"Error processing item {index+1}: {str(e)}")

        await browser.close()
        return contents

def create_pdf(contents):
    doc = SimpleDocTemplate("fisker_ocean_manual_debug.pdf", pagesize=letter)
    styles = getSampleStyleSheet()

    # Create custom styles only if they don't exist
    custom_styles = [
        ('Heading1', 18, 12),
        ('Heading2', 16, 10),
        ('Heading3', 14, 8),
        ('Heading4', 12, 6)
    ]

    for name, font_size, space_after in custom_styles:
        if name not in styles:
            styles.add(ParagraphStyle(name=name, fontSize=font_size, spaceAfter=space_after, keepWithNext=True))

    flowables = []

    title_style = ParagraphStyle(name='Title', parent=styles['Heading1'], alignment=TA_CENTER)
    flowables.append(Paragraph("Fisker Ocean Manual", title_style))
    flowables.append(Spacer(1, 36))

    for level, title, content in contents:
        heading_style = f'Heading{min(level + 1, 4)}'
        flowables.append(Paragraph(title, styles[heading_style]))
        flowables.append(Spacer(1, 12))
        flowables.append(Paragraph(content, styles['BodyText']))
        flowables.append(Spacer(1, 24))

    doc.build(flowables)

async def main():
    url = "https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html"
    contents = await scrape_website(url)
    create_pdf(contents)
    print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")

if __name__ == "__main__":
    asyncio.run(main())
