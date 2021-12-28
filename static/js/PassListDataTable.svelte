<script>
    import { location } from './stores.js';
    
    export let passes;


    function getDetailUrl(pass) {
        let params = {
            satid: pass.satid,
            name: $location.name,
            lat: $location.lat,
            lon: $location.lon,
            h: $location.h,
            aosdt: pass.start_pt.date.toISOString(),
        }
        return '/passes/detail/?' + new URLSearchParams(params).toString();
    }

    function goToDetailUrl(event) {
        const url = event.target.getAttribute("data-location");
        window.location.assign(url);
    };
    
    const monthDay = (pass) => pass.start_pt.getMonthDay;
    const timeMinutes = (pass) => pass.start_pt.getTimeMinutesParts.minute;
    const timeHour = (pass) => pass.start_pt.getTimeMinutesParts.hour;
    const timePeriod = (pass) => pass.start_pt.getTimeMinutesParts.dayPeriod;

</script>
    
<style lang="scss">
@import "static/sass/_variables.scss";

.data-table {
    border-collapse: collapse;
    text-align: left;
    margin: 0 auto;

    & thead {
        font-weight: 500;
    }

    & tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }

    & tr:hover {
        background-color: var(--primary-dark);
        color: white;
    }

    & td, th {
        padding: 0.5em 1.5em;
    }
}

.pass-time-ampm {
    font-size: 0.75em;
};
    
@media screen and (min-width: 550px) {
    .pass-time-ampm {
        font-size: 1em;
    };
}

</style>
    
<table class="data-table">
    <thead>
        <tr>
            <th>Date</th>
            <th>Duration</th>
            <th>Max Elevation</th>
        </tr>
    </thead>
    {#each passes as pass (pass.start_pt.date)}
        <tr on:click={goToDetailUrl} data-location={getDetailUrl(pass)}>
            <td>{monthDay(pass)}, {timeHour(pass)}:{timeMinutes(pass)} <span class='pass-time-ampm'>{timePeriod(pass)}</span></td>
            <td>{pass.duration}</td>
            <td>{pass.elevation.toString()}&deg;</td>
        </tr>
    {/each}
</table>
    
    
    