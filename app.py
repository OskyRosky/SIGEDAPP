##App ##

from flask import Flask, request, jsonify, render_template
import asyncio
import os
import re
import unicodedata
from urllib.parse import unquote
from playwright.async_api import async_playwright
import threading

app = Flask(__name__)

# 📂 Carpeta donde se guardarán los archivos automáticamente
BASE_DIR = r"C:\Users\Oscar Centeno\Desktop\Oscar\CGR\2025\SIGEDAPP"
DOWNLOAD_PATH = os.path.join(BASE_DIR, "Archivos")
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Función para limpiar nombres de archivo
def sanitize_filename(filename):
    filename = unquote(filename)
    filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode("ASCII")
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    return filename.strip()

# Extraer nombre de archivo desde los headers
async def get_filename_from_headers(response):
    content_disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename\*?=["\']?(?:UTF-8["\']*)?([^";]+)', content_disposition, re.IGNORECASE)
    if match:
        return sanitize_filename(match.group(1).strip())
    return None

# Función para descargar archivos
async def download_files(url):
    print("🚀 Iniciando Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("🔄 Cargando la página...")
        await page.goto(url, timeout=90000)
        print("✅ Página cargada con éxito")

        # Obtener todos los enlaces de documentos
        links = await page.locator("a").all()
        download_links = [link for link in links if "apex.navigation.dialog" in str(await link.get_attribute("href"))]

        if not download_links:
            print("❌ No se encontraron enlaces.")
            await browser.close()
            return "No se encontraron archivos."

        print(f"🔗 Se encontraron {len(download_links)} documentos para descargar.")

        base_url = "https://cgrweb.cgr.go.cr/apex/"
        for index, link in enumerate(download_links):
            print(f"📂 Abriendo documento {index + 1}...")

            async with context.expect_page() as new_page_info:
                await link.click()
            new_page = await new_page_info.value
            await new_page.wait_for_load_state("load")
            await new_page.wait_for_timeout(3000)

            embed_element = new_page.locator("embed")
            if await embed_element.count() > 0:
                file_url = await embed_element.get_attribute("src")
                full_url = base_url + file_url if not file_url.startswith("http") else file_url
                print(f"📄 Documento {index+1} encontrado: {full_url}")

                # Descargar el archivo
                file_response = await new_page.request.get(full_url)
                file_name = await get_filename_from_headers(file_response) or f"Documento_{index+1}.pdf"
                file_path = os.path.join(DOWNLOAD_PATH, file_name)

                with open(file_path, "wb") as f:
                    f.write(await file_response.body())

                print(f"✅ Documento {index+1} descargado como: {file_name}")

            else:
                print(f"❌ No se encontró un documento en el documento {index+1}.")

            await new_page.close()

        await browser.close()
        print("👋 Descarga completada.")
        return "Descarga completada."

# Ruta de la interfaz web
@app.route("/")
def index():
    return render_template("index.html")

# Ruta para iniciar la descarga
@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "Debe ingresar una URL válida."}), 400

    # Ejecutar la descarga en un hilo separado
    thread = threading.Thread(target=lambda: asyncio.run(download_files(url)))
    thread.start()

    return jsonify({"message": "Descarga en proceso. Los archivos se guardarán en la carpeta predeterminada."}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
