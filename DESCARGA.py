import sys
import asyncio
import os
import re
import unicodedata
from urllib.parse import unquote
from playwright.async_api import async_playwright

# 📂 Ruta de descarga en Windows (ajusta según necesites)
DOWNLOAD_PATH = os.path.join(os.environ["USERPROFILE"], "Downloads", "testdescarga")
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Función para limpiar los nombres de archivo
def sanitize_filename(filename):
    filename = unquote(filename)  # Decodificar caracteres URL
    filename = unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode("ASCII")  # Eliminar acentos
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)  # Caracteres no permitidos en Windows
    return filename.strip()

# Extraer el nombre del archivo desde los headers del servidor
async def get_filename_from_headers(response):
    content_disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename\*?=["\']?(?:UTF-8["\']*)?([^";]+)', content_disposition, re.IGNORECASE)
    if match:
        return sanitize_filename(match.group(1).strip())
    return None

async def main():
    print("🚀 Iniciando Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("🔄 Cargando la página principal...")
        await page.goto("https://cgrweb.cgr.go.cr/apex/f?p=CORRESPONDENCIA:1:::::P1_CONSECUTIVO:A88C108C63FD77A3C0E96E1EE8FC6802", timeout=90000)
        print("✅ Página cargada con éxito")

        # Obtener todos los enlaces de documentos
        links = await page.locator("a").all()
        download_links = [link for link in links if "apex.navigation.dialog" in str(await link.get_attribute("href"))]

        if not download_links:
            print("❌ No se encontraron enlaces de descarga.")
            await browser.close()
            return

        print(f"🔗 Se encontraron {len(download_links)} documentos para descargar.")

        base_url = "https://cgrweb.cgr.go.cr/apex/"  # Dominio base

        for index, link in enumerate(download_links):
            print(f"📂 Abriendo documento {index + 1}...")

            # Capturar la nueva ventana emergente
            async with context.expect_page() as new_page_info:
                await link.click()
            new_page = await new_page_info.value
            await new_page.wait_for_load_state("load")
            await new_page.wait_for_timeout(3000)  # Esperar por seguridad

            # Extraer la URL del documento desde el <embed>
            embed_element = new_page.locator("embed")
            if await embed_element.count() > 0:
                file_url = await embed_element.get_attribute("src")
                full_url = base_url + file_url if not file_url.startswith("http") else file_url
                print(f"📄 Documento {index+1} encontrado: {full_url}")

                # Solicitar el archivo y extraer el nombre original
                file_response = await new_page.request.get(full_url)
                file_name = await get_filename_from_headers(file_response)

                if not file_name:
                    file_name = f"Documento_{index+1}.pdf"  # Fallback si no se encuentra el nombre real

                # Guardar el archivo en la carpeta de descargas de Windows
                file_path = os.path.join(DOWNLOAD_PATH, file_name)
                with open(file_path, "wb") as f:
                    f.write(file_content)
                
                print(f"✅ Documento {index+1} descargado como: {file_name}")

            else:
                print(f"❌ No se encontró un documento en el documento {index+1}.")

            await new_page.close()  # Cerrar la ventana emergente

        await browser.close()
        print("👋 Proceso completado.")

# Ejecutar el script
if __name__ == "__main__":
    asyncio.run(main())