<script>
export let pass;
export let satellite;
export let location;

const detailUrl = '/passes/detail/?' + new URLSearchParams(
    {
        satid: satellite.id,
        satname: satellite.name,
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        h: location.h,
        aosdt: pass.start_pt.date.toISOString(),
    }
).toString();

function goToDetailUrl() {
    window.location.assign(detailUrl);
};

const monthDay = pass.start_pt.getMonthDay;
const timeMinutes = pass.start_pt.getTimeMinutesParts.minute;
const timeHour = pass.start_pt.getTimeMinutesParts.hour;
const timePeriod = pass.start_pt.getTimeMinutesParts.dayPeriod;
const timeHtml = `${timeHour}:${timeMinutes} <span class='pass-time-ampm'>${timePeriod}</span>`;

</script>

<style>
    /* your styles go here */
</style>

<div
    class="box is-rounded p-2 mb-3 pass-row"
    on:click={goToDetailUrl}
    data-location={detailUrl}
>
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
</div>