<script>
import { location } from './stores.js';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getVisibilityCircle, R_EARTH } from './passpredict.js';
// import circle from '@turf/circle';

// Ref: https://github.com/allyoucanmap/piano-map/blob/master/src/Map.svelte

export let satid;
export let aosdt;
export let losdt;
export let height;
export let width;

let map;
let latlng;
let visibilityRadius;

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

function resizeMap() {
    if(map) { 
        map.invalidateSize(); 
    }
}

async function fetchSatelliteLatLng() {
    const params = {
        satid: satid,
        aosdt: aosdt,
        losdt: losdt,
        dtsec: 30,
    }
    const resp = await fetch('/api/satellites/latlng/?' + new URLSearchParams(params).toString());
    const data = await resp.json();
    return data;
}

function setSatelliteCoordinateLine(map) {
    fetchSatelliteLatLng().then((data) => {
        map.eachLayer((layer) => {
            if (layer instanceof L.Polyline){
                layer.remove();
            }
        });
        latlng = data.latlng;
        visibilityRadius = data.radius;
        const satline = L.polyline(latlng, {
            color: lineColor,
            weight: 2,
        });
        const aospt = {lat: latlng[0][0], lon: latlng[0][1]};
        const r = distance($location, aospt);
        const circleLatlng = getVisibilityCircle($location, r, 120);
        const circle = L.polygon(circleLatlng, {
            color: '#666',
            weight: 2,
            fillColor: 'rgb(102, 102, 102)',
            fillOpacity: 0.2,
        });
        map.fitBounds(circle.getBounds());
        circle.addTo(map);
        satline.addTo(map);
    })
    return map;
}


function distance(point1, point2) {
    // Compute direct distance between two coordinates. Assume Earth is a sphere.
    const deg2rad = Math.PI / 180;
    const theta1 = (90 - point1.lat) * deg2rad;
    const theta2 = (90 - point2.lat) * deg2rad;
    const phi1 = point1.lon * deg2rad;
    const phi2 = point2.lon * deg2rad;
    const d = R_EARTH * Math.sqrt(2 - 2*(Math.sin(theta1)*Math.sin(theta2)*Math.cos(phi1 - phi2) + Math.cos(theta1)*Math.cos(theta2)));
    return d;
}

</script>

<style>
</style>

<svelte:window on:resize={resizeMap} />

<div class="map" style="width:{width}; height:{height}" use:mapAction></div>