<script>
import { format } from 'date-fns';
import { Pass } from './passpredict.js';
import { location as locationStore } from './stores.js';
import PassListItem from './PassListItem.svelte';
import PassListDataTable from './PassListDataTable.svelte';

export let satellite;
export let location;
export let start_date;
export let end_date;

const home_url = '/';
const static_url = '/static/';
const chevronUrl = static_url + 'img/fa-chevron-up.svg';

let showMaps = true;
let passes;

locationStore.set(location);

let params = {
    satid: satellite.id,
    lat: location.lat,
    lon: location.lon,
    h: location.h ? location.h : 0,
};

async function fetchPasses() {
    const response = await fetch('/api/passes/?' + new URLSearchParams(params).toString());
    const data = await response.json();
    passes = data.overpasses.map(pass => new Pass(pass));
    return passes;
}

let promise  = fetchPasses();

</script>

<style lang="scss">
@import "static/sass/_variables.scss";

.results-header {
    display: flex;
    flex-direction: row;
    justify-content: left;
    flex-wrap: wrap;
}

.results-header-left {
    flex-grow: 4;
}

.results-header-right {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
</style>


<div class="results-header">
    <div class="results-header-left">
        <div class="location-header">
            <span class="has-text-weight-semibold">Location: </span>
            {#if location.name }
                {location.name}
            {/if}
            <div class="is-size-7">
                <span class="has-text-weight-medium">Latitude:</span>&nbsp;{location.lat}&deg;&nbsp;
                <span class="has-text-weight-medium">Longitude:</span>&nbsp;{location.lon}&deg;
            </div>
        </div>
        <div class="satellite-header">
            <span class="has-text-weight-semibold">Satellite:</span>&nbsp;{satellite.name}
            <div class="is-size-7">
                <span class="has-text-weight-medium">NORAD ID:</span>&nbsp;{satellite.id}
            </div>
        </div>
        <div class="date-header">
            <span class="has-text-weight-semibold">Dates:</span>&nbsp;{format(start_date, 'P')}&nbsp;-&nbsp; {format(end_date, 'P')}
        </div>
    </div>
    <div class="results-header-right">
        <a class="button is-primary" href={home_url}>Search Again</a>
        <label for="showMaps">Show Maps</label>
        <input name="showMaps" type="checkbox" bind:checked={showMaps}/>

        <!-- <label for="visibleOnly" class="checkbox">
            <input id="visibleOnly" type="checkbox" checked />
            Visible Only
        </label> -->
    </div>
</div>


{#await promise}
<p class="is-size-5 has-text-centered mt-6 mb-4">
    Getting passes...
    <progress class="progress is-primary">50%</progress>
</p>
{:then passes}
    {#if passes.length > 0}
        {#if showMaps}
            {#each passes as pass (pass.start_pt.date)}
                    <PassListItem {satellite} {pass} {showMaps} />
            {/each}
        {:else}
            <PassListDataTable {passes} />
        {/if}
        <a href="" class="button is-floating is-primary">
            <img src={chevronUrl} alt="Up">
        </a>
    {:else}
        <p class="is-size-5 has-text-centered mt-6">
            No passes found
        </p>
    {/if}
{:catch error}
    <p class="is-size-5 has-text-centered has-text-danger mt-6">
        Error getting passes
    </p>
{/await}


