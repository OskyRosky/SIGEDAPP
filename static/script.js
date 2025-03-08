function startDownload() {
    const url = document.getElementById("url").value;
    if (!url) {
        alert("Por favor ingrese una URL válida.");
        return;
    }

    fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "url=" + encodeURIComponent(url)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("status").innerText = data.message;
        if (!data.error) {
            simulateProgress();
        }
    });
}

function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        document.getElementById("progress-bar").value = progress;
        document.getElementById("progress-text").innerText = `Descargando... ${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
            document.getElementById("progress-text").innerText = "Descarga completada!";
        }
    }, 500);
}
