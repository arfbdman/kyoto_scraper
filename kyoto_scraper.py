import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
from io import BytesIO  # To handle in-memory Excel files
from flask import Flask, request, render_template, jsonify, send_file
import openpyxl
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Manages ChromeDriver versions

app = Flask(__name__)

def extract_images_and_metadata(url):
    """Extract metadata and image URLs from a webpage using Selenium and BeautifulSoup."""
    try:
        # Configure Chromium options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")  # Required for Linux environments
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues

        # Dynamically resolve the Chromium binary location
        chromium_binary_path = os.environ.get("CHROMIUM_BIN", "/usr/bin/chromium-browser")
        chrome_options.binary_location = chromium_binary_path

        # Set up Selenium WebDriver with WebDriver Manager
        driver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)

        # Open the target URL
        driver.get(url)
        html_content = driver.page_source  # Get the page source
        driver.quit()  # Close the browser session

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract the page title
        title = soup.title.string if soup.title else "No Title Available"

        # Extract the project name from the URL
        project_name = urlparse(url).path.strip("/").split("/")[-1]

        # Extract all image URLs from the page
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
        return {
            "url": url,
            "error": str(e),
        }

def save_to_excel(data):
    """Save extracted data to an Excel file in memory."""
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Scraped Data"
    sheet.append(["URL", "Project Name", "Title", "Image URLs", "Error"])

    for row in data:
        url = row.get("url", "N/A")
        project_name = row.get("project_name", "N/A")
        title = row.get("title", "N/A")
        img_urls = "\n".join(row.get("image_urls", []))  # Join image URLs as a string
        error = row.get("error", "")

        sheet.append([url, project_name, title, img_urls, error])

    # Save the Excel file to an in-memory object
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file

@app.route("/")
def index():
    """Render the index HTML page."""
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    """Handle scraping requests."""
    urls = request.json.get("urls", [])
    if not urls:
        return jsonify({"error": "No URLs provided."}), 400

    # Scrape each URL
    results = []
    for url in urls:
        result = extract_images_and_metadata(url)
        results.append(result)

    # Save results to an Excel file
    excel_file = save_to_excel(results)

    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"Scraped_Data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)