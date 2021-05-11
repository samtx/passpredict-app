import {Point, getPassQuality} from "./passpredictlib.js";

const passList = document.getElementById('passList');
const visibleOnlyCheckbox = document.getElementById('visibleOnly');

const getPasses = async (satid, params) => {
    const response = await fetch(`/api/passes/${satid}?` +
        new URLSearchParams(params).toString()
    );
    const passResponse = await response.json();
    const passes = passResponse.overpasses;
    console.table(passes);
    return passes
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


visibleOnlyCheckbox.addEventListener('change', (event) => {
    let notVisiblePasses = document.querySelector('.not-visible');
    if (this.checked) {
        notVisiblePasses.hidden = true;
    }
    else {
        notVisiblePasses.hidden = false;
    }
})

const showPassList = (passes) => {
    if (passes.length == 0) {
        passList.innerHTML = `
            <p class="is-size-5 has-text-centered mt-6">
                No passes found
            </p>
        `
    }
    else {
        let html = '';
        for (const pass of passes) {
            const start_pt = new Point(pass.start_pt);
            const max_pt = new Point(pass.max_pt);
            const end_pt = new Point(pass.end_pt);
            const type = pass.type;
            const brightness = pass.brightness;
            html += `

            `
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
        .then((passes) => showPassList(passes))
        .catch(error => {
            console.error('Error getting passes: ' + error.message);
            showErrorMessage();
        });
})

