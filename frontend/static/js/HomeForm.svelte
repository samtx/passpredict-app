<script>
import AutoComplete from "simple-svelte-autocomplete";

export let formActionUrl;
export let satellites;

let location;
// let location = {name:'', lat:0, lon:0, h:0};

let name;  // location name
let lat;
let lon;
let h;
let satid;

function resetForm() {
    satid = undefined;
    location = undefined;
}


function getLocationFromFeature(feature){
    // Parse Mapbox Geocoding API response
    const name = feature['place_name'];
    const coords = feature['center'];
    const lon = coords[0];
    const lat = coords[1];
    return {name: name, lon: lon, lat: lat}
}

async function queryLocationAPI(search_text) {
    const params = {
        access_token:  "MAPBOX_ACCESS_TOKEN",
        autocomplete: true,
        types: [
            'postcode',
            'district',
            'place',
            'locality',
            'neighborhood',
            'address',
        ],
    };
    const base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/";
    const endpoint = encodeURIComponent(search_text);
    const response = await fetch(`${base_url}${endpoint}.json?` + new URLSearchParams(params).toString());
    const data = await response.json();
    const features = data.features;
    const locations = features.map(getLocationFromFeature);
    return locations;
}

function stringToFixedFloat(value, n) {
    if (value === ""){
        return ""
    }
    return parseFloat(value).toFixed(n);
}

// Update location variables with selected item data
$: if (location) {
        name = location.name;
        lat = location.lat;
        lon = location.lon;
        h = location.h;
    }
    else {
        name = null;
        lat = null;
        lon = null;
        h = null;
    }

$: latStr = stringToFixedFloat(lat, 4);
$: lonStr = stringToFixedFloat(lon, 4);

</script>

<style>

</style>

<form method="POST" action={formActionUrl}>
    <div class="field">
        <label for="locationSearch" class="label">Location</label>
        <AutoComplete
            searchFunction={queryLocationAPI}
            labelFieldName="name"
            localFiltering={false}
            placeholder="New York, NY"
            inputId="location-search"
            minCharactersToSearch=3
            html5autocomplete={true}
            dataFormType='other'
            lpIgnore={true}
            hideArrow={true}
            bind:selectedItem={location}
            className="is-arrowless"
        />
        {#if location}
            <div class="latlon-result">
                <span class="latlon">Latitude:</span> {latStr}&deg;
                &nbsp; &nbsp;
                <span class="latlon">Longitude:</span> {lonStr}&deg;
            </div>
        {/if}
    </div>

    <input type="hidden" name="name" bind:value={name} />
    <input type="hidden" name="lat" bind:value={lat} />
    <input type="hidden" name="lon" bind:value={lon} />
    <input type="hidden" name="h" bind:value={h} />

    <div class="field">
        <label for="satid" class="label">Select satellite</label>
        <span class="select">
            <select name="satid" bind:value={satid}>
                {#each satellites as satellite (satellite.id) }
                    <option value={satellite.id}>{satellite.name}</option>
                {/each}
            </select>
        </span>
     </div>

    <div class="buttons">
        <button id="submit" type="submit" class="button is-primary mr-5">Submit</button>
        <button id="reset" type="button" class="button" on:click|stopPropagation={resetForm}>Reset</button>
    </div>

</form>