<script>
import { location } from './stores.js';
import PassListItemMap from './PassListItemMap.svelte';

export let pass;
export let satellite;
export let showMaps = true;

let satid = satellite.id;
let aosdt = pass.start_pt.date.toISOString();
let losdt = pass.end_pt.date.toISOString();

let params = {
    satid: satid,
    name: $location.name,
    lat: $location.lat,
    lon: $location.lon,
    h: $location.h,
    aosdt: aosdt,
}

const detailUrl = '/passes/detail/?' + new URLSearchParams(params).toString();

function goToDetailUrl() {
    window.location.assign(detailUrl);
};

const monthDay = pass.start_pt.getMonthDay;
const timeMinutes = pass.start_pt.getTimeMinutesParts.minute;
const timeHour = pass.start_pt.getTimeMinutesParts.hour;
const timePeriod = pass.start_pt.getTimeMinutesParts.dayPeriod;
const durationStringArray = pass.duration.split(':');
const durationMinutes = durationStringArray[0];
const durationSeconds = durationStringArray[1];
</script>

<style lang="scss">
@import "static/sass/_variables.scss";

.pass-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
}

.pass-row:hover {
    background-color: var(--primary-dark);
    /* border: 1px solid var(--primary-dark); */
    font-weight: 500;
    color: white;
}

.data-header {
    font-weight: 500;
    margin-right: 1.25em;
}

.pass-item {
    text-align: right;
}

// .pass-data {
//     flex-grow: 1;
// }

table.pass-data {
    display: inline-table;
    border: 0;
    border-collapse: collapse;
    font-size: 0.9em;

    & td {
        padding-right: 0.4em;
    }
}

// .pass-data-row {
//     display: flex;
// }

.pass-map {
    width: 90vw;
    height: 40vh;
    margin: 1em 0;
}

.pass-time-ampm {
    font-size: 0.75em;
};

@media screen and (min-width: 550px) {
    .pass-time-ampm {
        font-size: 1em;
    };

    .pass-data {
        font-size: 1em;
        margin: 0 2em;

        & td {
            padding-right: 1em;
        }
    }

    .pass-map {
        width: 200px;
        height: 175px;
        flex-grow: 1;
        margin: 0;
    }
}

</style>

{#if showMaps}
    <div class="box is-rounded p-2 mb-3 pass-row" on:click={goToDetailUrl} data-location={detailUrl}>
        <table class="pass-data">
            <tr>
                <td class="data-header">Date:</td>
                <td>{monthDay}, {timeHour}:{timeMinutes} <span class='pass-time-ampm'>{timePeriod}</span></td>
            </tr>
            <tr>
                <td class="data-header">Duration:</td>
                <td>{durationMinutes} min, {durationSeconds} sec</td>
            </tr>
            <tr>
                <td class="data-header">Max elevation:</td>
                <td>{pass.elevation.toString()}&deg;</td>
            </tr>
        </table>
        <div class="pass-map">
            <PassListItemMap {satid} {aosdt} {losdt} height="100%" width="100%" />
        </div>
    </div>
{:else}
    <tr on:click={goToDetailUrl} data-location={detailUrl}>
        <td>{monthDay}, {timeHour}:{timeMinutes} <span class='pass-time-ampm'>{timePeriod}</span></td>
        <td>{pass.duration}</td>
        <td>{pass.elevation.toString()}&deg;</td>
    </tr>
{/if}
