import os
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify, send_file
import openpyxl
from io import BytesIO  # For handling in-memory files

app = Flask(__name__)

def extract_images_and_metadata(url):
    """Extract metadata and image URLs from the target webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title of the page
        title = soup.title.string if soup.title else "No Title Available"

        # Extract project name from URL
        project_name = urlparse(url).path.strip("/").split("/")[-1]

        # Extract all image URLs
        img_tags = soup.find_all("img")
        img_urls = [
            urljoin(url, img.get("src") or img.get("data-src") or img.get("data-lazy-src"))
            for img in img_tags if img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        ]

        return {
            "url": url,
            "title": title,
            "project_name": project_name,
            "image_urls": img_urls
        }
    except Exception as e:
        # Return the error as part of the result if anything goes wrong
        return {"url": url, "error": str(e)}

def save_to_excel(data):
    """Save extracted data to an in-memory Excel file."""
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Scraped Data"
    sheet.append(["URL", "Project Name", "Title", "Image URLs", "Error"])

    for row in data:
        url = row.get("url", "N/A")
        project_name = row.get("project_name", "N/A")
        title = row.get("title", "N/A")
        img_urls = "\n".join(row.get("image_urls", []))  # Join image URLs as newline-separated text
        error = row.get("error", "")

        sheet.append([url, project_name, title, img_urls, error])

    # Save the Excel file to an in-memory object
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

    # Scrape each URL and collect results
    results = []
    for url in urls:
        result = extract_images_and_metadata(url)
        results.append(result)

    # Generate an Excel file with the results
    excel_file = save_to_excel(results)

    # Return the file to the user as a downloadable response
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"Scraped_Data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)