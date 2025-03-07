#################
# SIGED con R   #
################


library(rvest)
library(httr)

# 📂 Directorio de descarga
download_dir <- "C:/Users/Oscar Centeno/Desktop/Oscar/CGR/2025/SIGEDAPP/Archivos"
dir.create(download_dir, showWarnings = FALSE, recursive = TRUE)

# URL base
base_url <- "https://cgrweb.cgr.go.cr/apex/f?p=CORRESPONDENCIA:1:::::P1_CONSECUTIVO:A88C108C63FD77A3C0E96E1EE8FC6802"

# Leer la página
cat("🔄 Cargando la página...\n")
page <- read_html(base_url)

# Extraer todos los enlaces
links <- page %>% html_nodes("a") %>% html_attr("href")

# Filtrar los enlaces de descarga
download_links <- links[grepl("apex.navigation.dialog", links)]
num_files <- length(download_links)

cat("🔗 Se encontraron", num_files, "archivos para descargar...\n")

# Descargar los archivos
for (i in seq_along(download_links)) {
  file_url <- paste0("https://cgrweb.cgr.go.cr", download_links[i]) # Convertir a URL completa
  file_name <- paste0("Archivo_", i, ".pdf")
  file_path <- file.path(download_dir, file_name)
  
  cat("📂 Descargando archivo:", file_name, "\n")
  
  tryCatch({
    GET(file_url, write_disk(file_path, overwrite = TRUE))
    cat("✅ Descargado:", file_name, "\n")
  }, error = function(e) {
    cat("❌ Error al descargar:", file_name, "\n")
  })
}

cat("👋 Descargas completadas.\n")
