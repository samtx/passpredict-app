import {Point, getPassQuality, formatMinutes} from "./passpredictlib.js";

const passList = document.getElementById('passList');
const visibleOnlyCheckbox = document.getElementById('visibleOnly');

const getPasses = async (satid, params) => {
    const response = await fetch(`/api/passes/${satid}?` +
        new URLSearchParams(params).toString()
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


visibleOnlyCheckbox.addEventListener('change', function(event) {
    let notVisiblePasses = document.querySelector('.not-visible');
    if (this.checked) {
        notVisiblePasses.hidden = true;
    }
    else {
        notVisiblePasses.hidden = false;
    }
})


const passListItemHtml = (pass) => {
    const html = `
        <div class="box is-rounded p-2 mb-3 pass-row pass-quality-${pass.quality}">
            <div class="p-1 pass-item pass-month-day">
                <p class="value">${pass.start_pt.getMonthDay}</p>
            </div>
            <div class="p-1 pass-item pass-time">
                <p class="value">${pass.start_pt.getTimeMinutes}</p>
            </div>
            <div class="p-1 pass-item pass-duration">
                <p class="value">${formatMinutes(pass.duration)}</p>
            </div>
            <div class="p-1 pass-item pass-max-el">
                <p class="value">${Math.round(pass.max_pt.elevation)}&deg;</p>
            </div>
        </div>
    `;
    return html;
};


const showPassList = (passes) => {
    if (passes.length == 0) {
        passList.innerHTML = `
            <p class="is-size-5 has-text-centered mt-6">
                No passes found
            </p>
        `
    }
    else {
        let html = "";
        for (const pass of passes) {
            // Refactor pass object for orbital_predictor return values
            const start_pt = new Point(pass.aos)
            const max_pt = new Point(pass.tca);
            const end_pt = new Point(pass.los);

            const duration = pass.duration;
            const type = pass.type;
            const brightness = pass.brightness ? pass.brightness : "";
            const quality = getPassQuality({type: pass.type, max_pt: max_pt});
            html += passListItemHtml({
                start_pt: start_pt,
                max_pt: max_pt,
                end_pt: end_pt,
                type: type,
                brightness: brightness,
                quality: quality,
                duration: duration,
            })
        }
        passList.innerHTML = html;
    }
}


const showErrorMessage = () => {
    passList.innerHTML = `
        <p class="is-size-5 has-text-centered has-text-danger mt-6">
            Error getting passes
        </p>
    `
};

document.addEventListener('DOMContentLoaded', () => {
    const url_string = (window.location.href).toLowerCase();
    const url = new URL(url_string);
    const pathArray = url.pathname.split('/');
    const satid = pathArray[pathArray.length - 1];
    const params = {
        lat: url.searchParams.get('lat'),
        lon: url.searchParams.get('lon'),
        // h: url.searchParams.get('h'),
    };
    getPasses(satid, params)
        .then((resp) => showPassList(resp.overpasses))
        .catch(error => {
            console.error('Error getting passes: ' + error.message);
            showErrorMessage();
        });
})
