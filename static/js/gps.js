document.getElementById("useGPS").addEventListener("change", function() {
    if (this.checked) {
        navigator.geolocation.getCurrentPosition(position => {
            document.getElementById("startLocation").value = `${position.coords.latitude},${position.coords.longitude}`;
        }, () => {
            alert("⚠️ GPS not available. Enter manually.");
            this.checked = false;
        });
    }
});
