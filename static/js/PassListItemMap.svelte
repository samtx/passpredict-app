<script>
import { location } from './stores.js';

// import MapboxVector from 'ol/layer/MapboxVector';

// Ref: https://github.com/allyoucanmap/piano-map/blob/master/src/Map.svelte

let map;

function initMap(node) {
    let map = new Map({
        view: new View({
            center: [$location.lon, $location.lat],
            zoom: 1
        }),
        layers: [
            new TileLayer({
                source: new OSM(),
            }),
        ],
        target: node,
    });

    return {
        destroy() {
            if (map) {
                map.setTarget(null);
                map = null;
            }
        }
    }
}
</script>

<style>
.map {
    width: 10em;
    height: 10em;
}
</style>

<svelte:head>
    <script src="https://cdn.jsdelivr.net/gh/openlayers/openlayers.github.io@master/en/v6.9.0/build/ol.js"/>
</svelte:head>
<div class="map" use:initMap></div>