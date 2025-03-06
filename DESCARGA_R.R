#################
# SIGED con R   #
################


library(RSelenium)
library(tidyverse)

# 📂 Directorio donde se guardarán los archivos
download_dir <- "C:/Users/Oscar Centeno/Desktop/Oscar/CGR/2025/SIGEDAPP/Archivos"

# URL base
base_url <- "https://cgrweb.cgr.go.cr/apex/f?p=CORRESPONDENCIA:1:::::P1_CONSECUTIVO:A88C108C63FD77A3C0E96E1EE8FC6802"

# Iniciar Selenium (asegúrate de que Chrome y ChromeDriver estén instalados)
rD <- rsDriver(browser = "chrome", chromever = "latest", port = 4567L)
remDr <- rD$client

# Abrir la página
remDr$navigate(base_url)
Sys.sleep(5)  # Espera que la página cargue

# Obtener todos los enlaces de descarga
links <- remDr$findElements(using = "css selector", "a")

# Filtrar solo los que contienen 'apex.navigation.dialog'
download_links <- links %>% keep(function(link) {
  href <- link$getElementAttribute("href")[[1]]
  !is.null(href) && grepl("apex.navigation.dialog", href)
})

# Contar archivos a descargar
num_files <- length(download_links)
cat("🔗 Se encontraron", num_files, "archivos para descargar...\n")

# Descargar archivos
for (i in seq_along(download_links)) {
  cat("📂 Descargando archivo", i, "...\n")
  
  # Abrir el enlace en una nueva pestaña
  download_links[[i]]$clickElement()
  Sys.sleep(3)  # Esperar que la nueva ventana cargue
  
  # Cambiar a la nueva pestaña
  windows <- remDr$getWindowHandles()
  remDr$switchToWindow(windows[[2]])
  
  # Buscar el elemento <embed> con la URL del archivo
  embed_element <- tryCatch({
    remDr$findElement(using = "css selector", "embed")
  }, error = function(e) NULL)
  
  if (!is.null(embed_element)) {
    file_url <- embed_element$getElementAttribute("src")[[1]]
    full_url <- ifelse(startsWith(file_url, "http"), file_url, paste0(base_url, file_url))
    
    cat("📄 Archivo encontrado:", full_url, "\n")
    
    # Descargar el archivo manualmente
    download.file(full_url, destfile = file.path(download_dir, paste0("Archivo_", i, ".pdf")), mode = "wb")
    cat("✅ Archivo", i, "descargado con éxito\n")
  } else {
    cat("❌ No se encontró documento en el archivo", i, "\n")
  }
  
  # Cerrar la pestaña y volver a la original
  remDr$closeWindow()
  remDr$switchToWindow(windows[[1]])
}

# Cerrar Selenium
remDr$close()
rD$server$stop()
cat("👋 Proceso completado.\n")
