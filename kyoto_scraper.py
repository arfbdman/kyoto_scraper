import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
from io import BytesIO  # For in-memory file handling
from flask import Flask, request, render_template, send_file, jsonify
import openpyxl
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Flask app
app = Flask(__name__)

def extract_images_and_metadata(url):
    """Extract metadata and image URLs from a webpage using Selenium and BeautifulSoup."""
    try:
        # Setup Selenium WebDriver (Headless Chrome)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
        chrome_options.add_argument("--no-sandbox")  # Required for some Linux environments
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Open the specified URL
        driver.get(url)
        html_content = driver.page_source
        driver.quit()  # Close the browser session

        # Parse the webpage
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract page title
        title = soup.title.string if soup.title else "No Title Available"

        # Extract project name from URL
        project_name = urlparse(url).path.strip("/").split("/")[-1]

        # Extract image URLs
        img_tags = soup.find_all("img")
        img_urls = [
            urljoin(url, img.get("src") or img.get("data-src") or img.get("data-lazy-src"))
            for img in img_tags if img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        ]

        return {
            "url": url,
            "title": title,
            "project_name": project_name,
            "image_urls": img_urls,
        }
    except Exception as e:
        # Return error message if the scraping fails
        return {
            "url": url,
            "error": str(e),
        }

def save_to_excel(data):
    """Save extracted data to an in-memory Excel file."""
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Scraped Data"
    sheet.append(["URL", "Project Name", "Title", "Image URLs", "Error"])  # Headers

    for row in data:
        url = row.get("url", "N/A")
        project_name = row.get("project_name", "N/A")
        title = row.get("title", "N/A")
        img_urls = "\n".join(row.get("image_urls", []))  # Join image URLs with line breaks
        error = row.get("error", "")

        sheet.append([url, project_name, title, img_urls, error])

    # Save Excel file to an in-memory object
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    urls = request.json.get("urls", [])
    if not urls:
        return jsonify({"error": "No URLs provided."}), 400

    # Scrape each URL and collect the results
    results = []
    for url in urls:
        result = extract_images_and_metadata(url)
        results.append(result)

    # Generate an Excel file from the results
    excel_file = save_to_excel(results)

    # Return the file as a downloadable response
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"Scraped_Data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)