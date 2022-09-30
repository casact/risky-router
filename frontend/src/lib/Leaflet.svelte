<script lang="ts">
  import { onMount } from "svelte";
  import L from "leaflet";
  import "leaflet-routing-machine";
  import "leaflet-control-geocoder";

  const apiUrl = import.meta.env.VITE_API_URL;
  const osrmUrl = import.meta.env.VITE_OSRM_URL;

  async function getFrequency(payload) {
    const response = await fetch(apiUrl + "/frequency", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    const per_x_vehicles = document.getElementById("per_x_vehicles");
    per_x_vehicles.textContent = new Intl.NumberFormat("en-US").format(
      data.per_x_vehicles
    );

    const return_period = document.getElementById("return_period");
    return_period.textContent = new Intl.NumberFormat("en-US").format(
      data.return_period
    );

    const return_period_plus_1 = document.getElementById(
      "return_period_plus_1"
    );
    return_period_plus_1.textContent = new Intl.NumberFormat("en-US").format(
      data.return_period_plus_1
    );
  }

  onMount(() => {
    var map = L.map("map");

    var Stadia_AlidadeSmooth = L.tileLayer(
      "https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 20,
        attribution:
          '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
      }
    );

    Stadia_AlidadeSmooth.addTo(map);

    function createButton(label, container) {
      var btn = L.DomUtil.create("button", "", container);
      btn.setAttribute("type", "button");
      btn.setAttribute("class", "rounded-md bg-space-cadet p-2 mx-2 text-white");
      btn.innerHTML = label;
      return btn;
    }

    var control = L.Routing.control({
      waypoints: [L.latLng(47.7619982, -122.3444731), L.latLng(47.6197677, -122.34880309)],
      lineOptions: {
        styles: [{ color: "#FB3640", opacity: 1, weight: 5 }],
      },
      routeWhileDragging: true,
      router: L.Routing.osrmv1({
        profile: "route/v1/driving",
        serviceUrl: osrmUrl,
      }),
      geocoder: L.Control.Geocoder.nominatim(),
    })
      // .on('routingstart', spinner.Spin())
      // .on('routesfound routingerror', spinner.Stop())
      .on("routeselected", function (e) {
        var route = e.route;
        getFrequency(route);
      })
      .addTo(map);

    map.on("click", function (e) {
      var container = L.DomUtil.create("div"),
        startBtn = createButton("Start from this location", container),
        destBtn = createButton("Go to this location", container);

      container.setAttribute("class", "flex");

      L.popup().setContent(container).setLatLng(e.latlng).openOn(map);

      L.DomEvent.on(startBtn, "click", function () {
        control.spliceWaypoints(0, 1, e.latlng);
        map.closePopup();
      });

      L.DomEvent.on(destBtn, "click", function () {
        control.spliceWaypoints(control.getWaypoints().length - 1, 1, e.latlng);
        map.closePopup();
      });
    });

    // body_type.addEventListener("input", function (e) {
    //   getSeverity(e.target.value);
    // });
  });
</script>

<svelte:head>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"
    integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="
    crossorigin=""
  />

  <script
    src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"
    integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="
    crossorigin="">
  </script>

  <script
    src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"
    crossorigin="">
  </script>

  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css"
  />

  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css"
  />
</svelte:head>
