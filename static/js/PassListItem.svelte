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
    satname: satellite.name,
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

table {
    display: inline-table;
    border: 0;
    border-collapse: collapse;
    font-size: 0.9em;
}

td {
    padding-right: 0.4em;
}

// .pass-data-row {
//     display: flex;
// }

.pass-map {
    width: 90vw;
    height: 40vh;
    margin: 1em 0;
}

.pass-month-day {
    flex-basis: 10%;
}

.pass-time {
    flex-basis: 20%;
}

.pass-time-ampm {
    font-size: 0.75em;
};

.pass-duration {
    flex-basis: 15%;
}

.pass-max-el {
    flex-basis: 10%;
}

@media screen and (min-width: 550px) {
    .pass-time-ampm {
        font-size: 1em;
    };

    table {
        font-size: 1em;
    }

    td {
        padding-right: 1em;
    }

    .pass-data {
        margin: 0 2em;
    }

    .pass-map {
        width: 200px;
        height: 175px;
        flex-grow: 1;
    }
}

</style>


<div
    class="box is-rounded p-2 mb-3 pass-row"
    on:click={goToDetailUrl}
    data-location={detailUrl}
>

    {#if showMaps}
        <table class="pass-data">
            <tr>
                <td class="data-header">Date:</td>
                <td>{monthDay}, {timeHour}:{timeMinutes} <span class='pass-time-ampm'>{timePeriod}</span></td>
            </tr>
            <tr>
                <td class="data-header">Pass duration:</td>
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
    {:else}
        <div class="p-1 pass-item pass-month-day">
            <p class="value">{monthDay}</p>
        </div>
        <div class="p-1 pass-item pass-time">
            <p class="value">{timeHour}:{timeMinutes} <span class='pass-time-ampm'>{timePeriod}</span></p>
        </div>
        <div class="p-1 pass-item pass-duration">
            <p class="value">{pass.duration}</p>
        </div>
        <div class="p-1 pass-item pass-max-el">
            <p class="value">{pass.elevation.toString()}&deg;</p>
        </div>
    {/if}

</div>