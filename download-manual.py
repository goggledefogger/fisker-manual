import asyncio
import os
import re
from playwright.async_api import async_playwright
import hashlib
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import base64
from io import BytesIO
from PIL import Image as PILImage

WAIT_SECONDS_BETWEEN_CLICKS = 1
WAIT_SECONDS_BETWEEN_IMAGES = 1

# Debug flag and section limit
DEBUG = False
DEBUG_SECTION_LIMIT = 100

def get_content_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

async def get_page_content(page):
    await page.wait_for_selector("#ohb_topic")

    content = await page.evaluate("""
        () => {
            const obj = document.querySelector('#ohb_topic');
            if (obj && obj.contentDocument) {
                const body = obj.contentDocument.body;

                // Exclude the header elements
                const headerElements = body.querySelectorAll('h1, h2, h3, h4, h5, h6');
                headerElements.forEach(el => el.remove());

                // Get the remaining text content
                const textContent = body.innerText;

                // Get the images
                const images = body.querySelectorAll('object[type="image/png"]');
                const imageSources = Array.from(images).map((img, idx) => {
                    const data = img.getAttribute('data');
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const image = new Image();
                    image.src = data;
                    canvas.width = image.width;
                    canvas.height = image.height;
                    ctx.drawImage(image, 0, 0);
                    const dataUrl = canvas.toDataURL('image/png');
                    return {data: dataUrl, filename: `image_${idx}.png`};
                });

                return { textContent, imageSources };
            }
            return { textContent: '', imageSources: [] };
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

        image_dir = "images"
        os.makedirs(image_dir, exist_ok=True)

        for index, item in enumerate(nav_items):
            try:
                section_title = await item.inner_text()

                # Sanitize the section title to create a valid filename
                section_title = re.sub(r'[\\/*?:"<>|]', "_", section_title)
                level = len(await item.query_selector_all("xpath=ancestor::ul"))

                await item.click()
                await asyncio.sleep(WAIT_SECONDS_BETWEEN_CLICKS)  # Wait for content to load

                content = await get_page_content(page)
                content_hash = get_content_hash(content['textContent'])

                print(f"Processing: {section_title}")
                print(f"Content hash: {content_hash}")
                print("Content preview: {}...".format(content['textContent'][:100].replace('\n', ' ')))

                if content_hash in processed_content_hashes:
                    print(f"Skipping duplicate content: {section_title}")
                    continue

                # Save the images
                image_sources = []
                for i, image_source in enumerate(content['imageSources']):
                    image_filename = f"{section_title}_{image_source['filename']}"
                    image_path = os.path.join(image_dir, image_filename)

                    # if the file already exists, check if the size of the file
                    # is non-zero and if so skip it. otherwise continue and
                    # try to save the image again
                    if os.path.exists(image_path):
                        if os.path.getsize(image_path) > 0:
                            print(f"Skipping existing image: {image_path}")
                            image_sources.append(image_path)
                            continue

                    print(f"Saving embedded image: {image_filename}")

                    # wait for image to be done downloading locally
                    await asyncio.sleep(WAIT_SECONDS_BETWEEN_IMAGES)

                    # Decode base64 image data
                    image_data = base64.b64decode(image_source['data'].split(',')[1])
                    print(f"Image data length for {image_filename}: {len(image_data)}")
                    with open(image_path, 'wb') as handler:
                        handler.write(image_data)
                    print(f"Saved image: {image_path}")
                    image_sources.append(image_path)

                contents.append((level, section_title, content['textContent'], image_sources))
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

    for level, title, content, image_sources in contents:
        heading_style = f'Heading{min(level + 1, 4)}'
        flowables.append(Paragraph(title, styles[heading_style]))
        flowables.append(Spacer(1, 12))

        # Split content around images
        content_parts = re.split(r'\[IMAGE\]', content)
        content_index = 0

        for image_path in image_sources:
            if os.path.exists(image_path):
                try:
                    img = PILImage.open(image_path)

                    # Calculate the maximum width and height
                    max_width = 400
                    max_height = 500  # Adjust this value as needed

                    # Calculate the scaling factor
                    width_ratio = max_width / img.width
                    height_ratio = max_height / img.height
                    scale_factor = min(width_ratio, height_ratio)

                    # Calculate new dimensions
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)

                    # Add text before the image if any
                    if content_index < len(content_parts):
                        part = content_parts[content_index].strip()
                        if part:
                            flowables.append(Paragraph(part, styles['BodyText']))
                            flowables.append(Spacer(1, 12))
                        content_index += 1

                    # Add image
                    img_flowable = Image(image_path, width=new_width, height=new_height)
                    flowables.append(img_flowable)
                    flowables.append(Spacer(1, 12))
                except Exception as e:
                    print(f"Error adding image {image_path}: {str(e)}")
                    # If there's an error, add a placeholder text
                    flowables.append(Paragraph(f"[Image: {os.path.basename(image_path)}]", styles['BodyText']))
                    flowables.append(Spacer(1, 12))
            else:
                print(f"Image file not found: {image_path}")
                flowables.append(Paragraph(f"[Missing Image: {os.path.basename(image_path)}]", styles['BodyText']))
                flowables.append(Spacer(1, 12))

        # Add remaining text after images
        while content_index < len(content_parts):
            part = content_parts[content_index].strip()
            if part:
                flowables.append(Paragraph(part, styles['BodyText']))
                flowables.append(Spacer(1, 12))
            content_index += 1

    try:
        doc.build(flowables)
        print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")
    except Exception as e:
        print(f"Error building PDF: {str(e)}")

async def main():
    url = "https://www.fiskerinc.com/owners_manual/Ocean/content/en-us/owner_guide.html"
    contents = await retrieve_website_content(url)
    create_pdf(contents)
    print(f"PDF created: fisker_ocean_manual_debug.pdf with {len(contents)} unique sections")

if __name__ == "__main__":
    asyncio.run(main())
