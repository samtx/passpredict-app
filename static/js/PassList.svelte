<script>
import { format } from 'date-fns';
import { Pass } from './passpredict.js';
import PassListItem from './PassListItem.svelte';

export let satellite;
export let location;
export let start_date;
export let end_date;

let home_url = '/';
let static_url = '/static/';

let showMaps = true;
let passes;
const chevronUrl = static_url + 'img/fa-chevron-up.svg';


async function fetchPasses(params) {
    const response = await fetch('/api/passes/?' + new URLSearchParams(params).toString());
    const data = await response.json();
    passes = data.overpasses.map(pass => new Pass(pass));
    return passes;
}

let params = {
    satid: satellite.id,
    lat: location.lat,
    lon: location.lon,
    h: location.h ? location.h : 0,
};

let promise = fetchPasses(params);

</script>

<style>
    /* your styles go here */
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

            <label for="showMaps" class="checkbox">
                <input id="showMaps" type="checkbox" bind:checked={showMaps}/>
                Show Maps
            </label>

        <!-- <label for="visibleOnly" class="checkbox">
            <input id="visibleOnly" type="checkbox" checked />
            Visible Only
        </label> -->
    </div>
</div>

<div id="passListHeader" class="p-2 mb-1">
    <p class="pass-item pass-month-day">Date</p>
    <p class="pass-item pass-time">Time</p>
    <p class="pass-item pass-duration">Duration</p>
    <p class="pass-item pass-max-el">Max Elevation</p>
</div>

{#await promise}
<p class="is-size-5 has-text-centered mt-6 mb-4">
    Getting passes...
    <progress class="progress is-primary">50%</progress>
</p>
{:then passes}
    {#if passes.length > 0}
        {#each passes as pass (pass.start_pt.date)}
            <PassListItem satellite={satellite} location={location} pass={pass} />
        {/each}
        <a href="#" class="button is-floating is-primary">
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


