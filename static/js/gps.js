document.getElementById("useGPS").addEventListener("change", function() {
    if (this.checked) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                let lat = position.coords.latitude;
                let lon = position.coords.longitude;
                document.getElementById("startLocation").value = `${lat},${lon}`;
            },
            function(error) {
                alert("⚠️ GPS error: Please enter your location manually.");
                document.getElementById("useGPS").checked = false;
            }
        );
    }
});
