<script>
import { location } from './stores.js';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Ref: https://github.com/allyoucanmap/piano-map/blob/master/src/Map.svelte

export let satid;
export let aosdt;

let map;

let markerColor = "#6495ED";
let lineColor = "#D2042D";

// let mapStyle = 'mapbox/streets-v11';
let mapStyle = 'mapbox/light-v10';

function setTileLayer(map) {
    // Remove existing tile layer
    map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer){
            layer.remove();
        }
    });
    // Add new layer
    L.tileLayer('https://api.mapbox.com/styles/v1/{styleId}/tiles/{tileSize}/{z}/{x}/{y}?access_token={accessToken}', {
        attribution: '© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>',
        tileSize: 512,
        maxZoom: 18,
        zoomOffset: -1,
        styleId: mapStyle,
        accessToken: "MAPBOX_ACCESS_TOKEN",
    }).addTo(map);
    return map;
}

const locationIcon = L.icon({
    iconUrl: "/static/img/map-marker.svg",
    iconSize: [16, 32],
    iconAnchor: [8, 32],
});

// const icon = L.icon({
//     iconUrl: "/static/img/marker-icon.png",
//     iconRetinaUrl: "/static/img/marker-icon-2x.png",
//     shadowUrl: "/static/img/marker-shadow.png",
// })

function setLocationMarker(map) {
    L.marker([$location.lat, $location.lon], {icon: locationIcon}).addTo(map);
    return map;
}

function initMap(container) {
    let m = L.map(container, {
        attributionControl: false,
        center: [$location.lat, $location.lon],
        zoom: 3,
        // Disable zoom and pan. Make it a static map image
        zoomControl: false,
        dragging: false,
        boxZoom: false,
        doubleClickZoom: false,
        keyboard: false,
        scrollWheelZoom: false,
        tap: false,
        touchZoom: false,
    });
    setTileLayer(m);
    setLocationMarker(m);
    setSatelliteCoordinateLine(m);
    return m;
}

function mapAction(container) {
    map = initMap(container);
    return {
        destroy() {
            map.remove();
        }
    }
}

async function fetchSatelliteCoordinates() {
    let params = {
        satid: satid,
        lat: $location.lat,
        lon: $location.lon,
        h: $location.h,
        aosdt: aosdt,
    }
    let resp = await fetch('/api/passes/detail/?' + new URLSearchParams(params).toString());
    let data = await resp.json();
    return {lat: data.satellite.latitude, lon: data.satellite.longitude};
}

function setSatelliteCoordinateLine(map) {
    fetchSatelliteCoordinates().then((coords) => {
        let latlngs = [];
        const n = coords.lat.length;
        for (let i = 0; i < n; i++) {
            latlngs.push([coords.lat[i], coords.lon[i]]);
        };
        map.eachLayer((layer) => {
        if (layer instanceof L.Polyline){
            layer.remove();
        }
    });
        L.polyline(latlngs, {color: lineColor}).addTo(map);
    })
    return map;

}

</script>

<style>
.map {
    width: 250px;
    height: 250px;
}
</style>

<div class="map" use:mapAction></div>