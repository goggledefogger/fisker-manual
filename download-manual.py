import asyncio
import os
import re
from playwright.async_api import async_playwright
import hashlib
from weasyprint import HTML
import base64
from io import BytesIO
from PIL import Image as PILImage

WAIT_SECONDS_BETWEEN_CLICKS = 1
WAIT_SECONDS_BETWEEN_IMAGES = 2

# Debug flag and section limit
DEBUG = False
DEBUG_SECTION_LIMIT = 100

def get_content_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

async def get_page_content(page):
    await page.wait_for_selector("#ohb_topic")

    content = await page.evaluate("""
        async () => {
            const obj = document.querySelector('#ohb_topic');
            if (obj && obj.contentDocument) {
                const body = obj.contentDocument.body;

                // Ensure images are fully loaded
                const imgElements = body.querySelectorAll('img');
                for (const img of imgElements) {
                    if (!img.complete) {
                        const promise = new Promise((resolve) => {
                            img.onload = resolve;
                            img.onerror = resolve;
                        });
                        await promise;
                    }
                }

                // Get the HTML content including styles
                const htmlContent = obj.contentDocument.documentElement.outerHTML;

                return { htmlContent };
            }
            return { htmlContent: '' };
        }
    """)

    return content

async def retrieve_website_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_selector("#navigation_bar")

        nav_items = await page.query_selector_all("#navigation_bar li")

        contents = []
        processed_content_hashes = set()
        processed_count = 0

        for index, item in enumerate(nav_items):
            try:
                section_title = await item.inner_text()

                # Sanitize the section title to create a valid filename
                section_title = re.sub(r'[\\/*?:"<>|]', "_", section_title)
                level = len(await item.query_selector_all("xpath=ancestor::ul"))

                await item.click()
                await asyncio.sleep(WAIT_SECONDS_BETWEEN_CLICKS)  # Wait for content to load

                content = await get_page_content(page)
                content_hash = get_content_hash(content['htmlContent'])

                print(f"Processing: {section_title}")
                print(f"Content hash: {content_hash}")
                print("Content preview: {}...".format(content['htmlContent'][:100].replace('\n', ' ')))

                if content_hash in processed_content_hashes:
                    print(f"Skipping duplicate content: {section_title}")
                    continue

                contents.append((level, section_title, content['htmlContent']))
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
    html_content = "<html><body>"

    for level, title, content in contents:
        html_content += f"<h{min(level + 1, 6)}>{title}</h{min(level + 1, 6)}>"
        html_content += content

    html_content += "</body></html>"

    HTML(string=html_content).write_pdf("fisker_ocean_manual_debug.pdf")
    print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")

async def main():
    url = "https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html"
    contents = await retrieve_website_content(url)
    create_pdf(contents)
    print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")

if __name__ == "__main__":
    asyncio.run(main())
