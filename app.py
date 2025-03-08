##App ##

from flask import Flask, render_template, request, jsonify
import os
import asyncio
from playwright.async_api import async_playwright
import threading

app = Flask(__name__)

# 📂 Carpeta donde se guardarán los archivos descargados
DOWNLOAD_PATH = os.path.join(os.getcwd(), "Archivos")
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Función para descargar los archivos
async def download_files(url, progress_callback):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(url, timeout=90000)

        links = await page.locator("a").all()
        download_links = [link for link in links if "apex.navigation.dialog" in str(await link.get_attribute("href"))]

        if not download_links:
            await browser.close()
            return "No se encontraron enlaces de descarga."

        total_files = len(download_links)
        base_url = "https://cgrweb.cgr.go.cr/apex/"

        for index, link in enumerate(download_links):
            async with context.expect_page() as new_page_info:
                await link.click()
            new_page = await new_page_info.value
            await new_page.wait_for_load_state("load")
            await new_page.wait_for_timeout(3000)

            embed_element = new_page.locator("embed")
            if await embed_element.count() > 0:
                file_url = await embed_element.get_attribute("src")
                full_url = base_url + file_url if not file_url.startswith("http") else file_url

                file_response = await new_page.request.get(full_url)
                file_name = f"Archivo_{index+1}.pdf"

                file_content = await file_response.body()
                file_path = os.path.join(DOWNLOAD_PATH, file_name)
                with open(file_path, "wb") as f:
                    f.write(file_content)

                progress_callback(index + 1, total_files)

            await new_page.close()
        await browser.close()
        return "Descarga completada con éxito."

# Iniciar descarga en un hilo separado para no bloquear Flask
def start_download_thread(url):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(download_files(url, lambda completed, total: print(f"Progreso: {completed}/{total}")))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "Debe ingresar un enlace válido."})

    thread = threading.Thread(target=start_download_thread, args=(url,))
    thread.start()

    return jsonify({"message": "Descarga en proceso..."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
