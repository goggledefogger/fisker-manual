import asyncio
from pyppeteer import launch
import pdfkit

async def scrape_website(url):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, waitUntil='networkidle0')

    # Extract all menu items
    menu_items = await page.evaluate('''
        () => {
            const items = [];
            document.querySelectorAll('.topiclink').forEach(link => {
                const onclick = link.getAttribute('onclick');
                let url = '';
                if (onclick) {
                    const match = onclick.match(/newSrc\('(.+?)'/);
                    if (match) {
                        url = match[1];
                    }
                }
                items.push({
                    title: link.innerText,
                    url: url
                });
            });
            return items;
        }
    ''')

    content = []
    for item in menu_items:
        if item['url']:
            # Simulate clicking on each menu item
            await page.evaluate(f"newSrc('{item['url']}', newSrcEnum.SIDE_NAV_CLICK)")
            await page.waitForSelector('#ohb_topic')

            # Extract content
            item_content = await page.evaluate('''
                () => {
                    const frame = document.querySelector('#ohb_topic');
                    if (frame && frame.contentDocument) {
                        return frame.contentDocument.body.innerHTML;
                    }
                    return '';
                }
            ''')
            content.append((item['title'], item_content))

    await browser.close()
    return content

def create_pdf(content, output_filename):
    toc = "<h1>Table of Contents</h1><ul>"
    full_content = ""

    for i, (title, item_content) in enumerate(content):
        toc += f'<li><a href="#section{i}">{title}</a></li>'
        full_content += f'<h1 id="section{i}">{title}</h1>{item_content}'

    toc += "</ul>"

    full_html = f"<html><body>{toc}{full_content}</body></html>"

    pdfkit.from_string(full_html, output_filename)

async def main():
    url = "https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html"  # Replace with the actual URL if different
    content = await scrape_website(url)
    create_pdf(content, "owners_manual.pdf")

asyncio.get_event_loop().run_until_complete(main())
