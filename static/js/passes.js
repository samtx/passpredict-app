import {Point, getPassQuality, formatMinutes} from "./passpredictlib.js";

const passList = document.getElementById('passList');
const visibleOnlyCheckbox = document.getElementById('visibleOnly');

const getPasses = async (params) => {
    const response = await fetch('/api/passes/?' + new URLSearchParams(params).toString()
    );
    const data = await response.json();
    console.log(data);
    return data
};

const filterVisibleOnlyPasses = (visibleOnly, passes) => {
    let filteredPasses;
    if (visibleOnly) {
        filteredPasses = passes.filter((pass) => pass.type == "visible");
    } else {
        filteredPasses = passes;
    }
    return filteredPasses;
};


// visibleOnlyCheckbox.addEventListener('change', function(event) {
//     let notVisiblePasses = document.querySelector('.not-visible');
//     if (this.checked) {
//         notVisiblePasses.hidden = true;
//     }
//     else {
//         notVisiblePasses.hidden = false;
//     }
// })


const showPassList = (resp, locationName) => {
    if (resp.overpasses.length == 0) {
        passList.innerHTML = `
            <p class="is-size-5 has-text-centered mt-6">
                No passes found
            </p>
        `
    }
    else {
        passList.innerHTML = "";
        resp.location.name = locationName;
        for (const pass of resp.overpasses) {
            // Refactor pass object for orbital_predictor return values
            const start_pt = new Point(pass.aos)
            const max_pt = new Point(pass.tca);
            const end_pt = new Point(pass.los);

            const duration = pass.duration;
            const type = pass.type;
            const brightness = pass.brightness ? pass.brightness : "";
            const quality = getPassQuality({type: pass.type, max_pt: max_pt});
            const passRowDiv = document.createElement('div');
            passRowDiv.classList.add('box', 'is-rounded', 'p-2', 'mb-3', 'pass-row');
            passRowDiv.setAttribute('data-location', getPassDetailUrl(resp.satellite, resp.location, pass))
            const timeParts = start_pt.getTimeMinutesParts;
            const timeMinutes = timeParts.minute;
            const timeHour = timeParts.hour;
            const timePeriod = timeParts.dayPeriod;
            passRowDiv.innerHTML = `
                <div class="p-1 pass-item pass-month-day">
                    <p class="value">${start_pt.getMonthDay}</p>
                </div>
                <div class="p-1 pass-item pass-time">
                    <p class="value">${timeHour}:${timeMinutes} <span class="pass-time-ampm">${timePeriod}</span></p>
                </div>
                <div class="p-1 pass-item pass-duration">
                    <p class="value">${formatMinutes(duration)}</p>
                </div>
                <div class="p-1 pass-item pass-max-el">
                    <p class="value">${Math.round(max_pt.elevation)}&deg;</p>
                </div>
            `;
            passRowDiv.addEventListener('click', (event) => {
                // Bubble up to parent nodes to find data-location attribute.
                // The event.target will be the element that was clicked, so it
                // could be the <p> tag or the row <div>
                let url;
                let node = event.target;
                do {
                    url = node.getAttribute('data-location');
                    node = node.parentElement;
                } while (url == null);
                window.location.assign(url);
            });
            passList.appendChild(passRowDiv);
        }
    }
}


const showErrorMessage = () => {
    passList.innerHTML = `
        <p class="is-size-5 has-text-centered has-text-danger mt-6">
            Error getting passes
        </p>
    `
};


const getPassDetailUrl = (satellite, location, pass) => {
    const params = {
        satid: satellite.id,
        satname: satellite.name,
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        h: location.h,
        aosdt: pass.aos.datetime,
    }
    const url = '/passes/detail/?' + new URLSearchParams(params).toString()
    return url
};


document.addEventListener('DOMContentLoaded', () => {
    const url_string = (window.location.href).toLowerCase();
    const url = new URL(url_string);
    const name = url.searchParams.get('name');  // location name
    const params = {
        satid: url.searchParams.get('satid'),
        lat: url.searchParams.get('lat'),
        lon: url.searchParams.get('lon'),
        h: url.searchParams.get('h') ? url.searchParams.get('h') : 0,
    };
    getPasses(params)
        .then((resp) => showPassList(resp, name))
        .catch(error => {
            console.error('Error getting passes: ' + error.message);
            showErrorMessage();
        });
})
