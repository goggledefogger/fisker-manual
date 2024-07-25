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
                return obj.contentDocument.body.innerText;
            }
            return '';
        }
    """)

    title = await page.evaluate("""
        () => {
            const obj = document.querySelector('#ohb_topic');
            if (obj && obj.contentDocument) {
                const h1 = obj.contentDocument.querySelector('h1');
                return h1 ? h1.innerText : document.title;
            }
            return document.title;
        }
    """)

    return title, content

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
                await item.click()
                await asyncio.sleep(2)

                title, content = await get_content(page)
                content_hash = get_content_hash(content)

                if content_hash in processed_content_hashes:
                    print(f"Skipping duplicate content: {title}")
                    continue

                contents.append((title, content))
                processed_content_hashes.add(content_hash)
                processed_count += 1
                print(f"Processed [{processed_count}/{len(nav_items)}]: {title}")

                content_preview = content[:100].replace('\n', ' ') + '...'
                print(f"Content preview: {content_preview}")

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
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    flowables = []

    # Add title page
    flowables.append(Paragraph("Fisker Ocean Manual", styles['Title']))
    flowables.append(Spacer(1, 36))

    for title, content in contents:
        flowables.append(Paragraph(title, styles['Heading1']))
        flowables.append(Spacer(1, 12))
        paragraphs = content.split('\n')
        for para in paragraphs:
            if para.strip():
                flowables.append(Paragraph(para, styles['BodyText']))
                flowables.append(Spacer(1, 6))
        flowables.append(Spacer(1, 24))

    doc.build(flowables)

async def main():
    url = "https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html"
    contents = await scrape_website(url)
    create_pdf(contents)
    print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")

if __name__ == "__main__":
    asyncio.run(main())
