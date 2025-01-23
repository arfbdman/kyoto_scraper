import os
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify, send_file
import openpyxl
import zipfile
import io

def create_directory(folder_name):
    """Create directory if it doesn't exist."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def download_file(url, folder_name, image_format):
    """Download file from a URL into format-specific folders."""
    try:
        # Get the filename from the URL
        filename = os.path.basename(url.split("?")[0])
        extension = filename.split(".")[-1].lower() if "." in filename else "unknown"

        # Make a subfolder for the image format (like 'jpg', 'png', etc.)
        format_folder = os.path.join(folder_name, image_format)
        create_directory(format_folder)

        # Save the file in the correct folder
        file_path = os.path.join(format_folder, filename)
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        return f"Downloaded: {file_path}"
    except Exception as e:
        return f"Failed to download {url}: {e}"

def extract_images_and_metadata(url, output_folder):
    """Extract images from a webpage and fetch metadata (title, project name)."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract page title
        title = soup.title.string if soup.title else "No Title Available"

        # Extract project name from the URL
        project_name = urlparse(url).path.strip("/").split("/")[-1]

        # Create a folder for this project using the project name
        project_folder = os.path.join(output_folder, project_name)
        create_directory(project_folder)

        # Extract image URLs from the page
        img_tags = soup.find_all("img")
        img_urls = [urljoin(url, img.get("src") or img.get("data-src") or img.get("data-lazy-src"))
                    for img in img_tags if img.get("src") or img.get("data-src") or img.get("data-lazy-src")]

        # Download each image into the correct format subfolder
        for img_url in img_urls:
            extension = os.path.basename(img_url.split("?")[0]).split(".")[-1].lower()
            extension = extension if extension in ["jpg", "jpeg", "png", "gif", "bmp", "webp"] else "unknown"
            download_file(img_url, project_folder, extension)

        return {"title": title, "project_name": project_name, "folder": project_folder}
    except Exception as e:
        return {"error": str(e)}

def save_to_excel(data, output_folder):
    """Save extracted data to an Excel file."""
    excel_file_path = os.path.join(output_folder, "Scraped_Data.xlsx")
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Scraped Data"
    sheet.append(["URL", "Project Name", "Title"])
    for row in data:
        sheet.append([row["url"], row["project_name"], row["title"]])
    wb.save(excel_file_path)
    return excel_file_path

def create_zip(output_folder):
    """Create a ZIP file from the output folder."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=output_folder)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer

# Flask setup
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Front-end HTML form (template)

@app.route('/scrape', methods=['POST'])
def scrape():
    urls = request.json.get("urls", [])
    if not urls:
        return jsonify({"error": "No URLs provided."}), 400

    # Create output folder with timestamp
    output_folder = f"Downloaded_Media_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    create_directory(output_folder)

    results = []
    for url in urls:
        result = extract_images_and_metadata(url, output_folder)
        result["url"] = url
        results.append(result)

    # Save the data to an Excel file
    excel_file_path = save_to_excel(results, output_folder)

    # Create a ZIP archive of all files
    zip_file = create_zip(output_folder)

    # Send the ZIP file as a downloadable file
    return send_file(zip_file, download_name="scraped_data.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)