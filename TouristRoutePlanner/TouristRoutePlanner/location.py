import streamlit as st
import streamlit.components.v1 as components


def get_current_location():
    components.html(
        """
        <script>
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                document.body.innerHTML =
                    "<p>Latitude: " + lat +
                    "<br>Longitude: " + lon + "</p>";
            },
            function(error) {
                document.body.innerHTML =
                    "<p>Location access was not allowed.</p>";
            }
        );
        </script>
        """,
        height=100
    )