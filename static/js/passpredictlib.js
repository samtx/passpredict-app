// module for passpredict javascript functions

export class Point {
    constructor(obj) {
        this.date = new Date(obj.datetime);  // datetime string
        this.azimuth = obj.az;
        this.elevation = obj.el;
        this.range = obj.range;
        this.brightness = obj.brightness;
    }

    get getMonthDay() {
        const d = new Intl.DateTimeFormat([], { dateStyle: "short" }).format(this.date);
        const dateString = d.split("/").slice(0, 2).join("/");
        return dateString;
    }

    get getTimeMinutesParts() {
        const partsArray = new Intl.DateTimeFormat([], { timeStyle: "short" }).formatToParts(this.date);
        let partsObject = {}
        for (let i = 0; i < partsArray.length; i++) {
            partsObject[partsArray[i].type] = partsArray[i].value;
        }
        return partsObject;
    }

    get getTime() {
        const t = new Intl.DateTimeFormat([], { timeStyle: "medium" }).format(this.date);
        return t;
    }
}


export const getPassQuality = (pass) => {
    if (pass.type !== 'visible') {
        return 0
    }
    if (pass.max_pt.elevation > 70) {
        return 1
    }
    if (pass.max_pt.elevation > 45) {
        return 2
    }
    if (pass.max_pt.elevation > 10) {
        return 3
    }
}


async function queryLocationAPI(search_text) {
    const url = `locations/`;
    const response = await fetch(
        url + "?" + new URLSearchParams({q: search_text}).toString()
    );
    const locations = await response.json();
    return locations;
}


export const getLocations = async (query) => {
    const data = await queryLocationAPI(query);
    return data['locations'];
};


const regExpEscape = (s) => {
    // From https://github.com/elcobvg/svelte-autocomplete/blob/master/src/index.html
    return s.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&")
  }


export const markQuerySubstring = (query, string) => {
    query = regExpEscape(query);
    string = string.replace(new RegExp(query, 'gmi'), `<strong>${query}</strong>`);
    return string
}

export const formatMinutes = (total_seconds) => {
    // Return string of MM:SS
    let minutes = total_seconds / 60.0
    let seconds = total_seconds - Math.floor(minutes) * 60;
    seconds = seconds.toFixed(0);
    let seconds_str = padZeros(seconds, 2);
    let s = `${minutes.toFixed(0)}:${seconds_str}`
    return s;
}


const padZeros = (n, size) => {
    let nstr = n.toString();
    while (nstr.length < size) {
        nstr = "0" + nstr;
    }
    return nstr
}


export const round = (x, n) => {
};


export const getPasses = async (params) => {
    const response = await fetch(
        '/api/passes/?' + new URLSearchParams(params).toString()
    );
    const data = await response.json();
    console.log(data);
    return data
};


export function passesFormComponent() {
    return {
        query: "",
        data: initData(),
        selectedIndex: null,
        focusedIndex: null,
        open: false,

        init: function () {
            // check localstorage for previous search query
            let query = localStorage.getItem('location-query');
            if (query) {
                this.query = query;
                this.data[0].lat = localStorage.getItem('location-lat');
                this.data[0].lon = localStorage.getItem('location-lon');
                this.data[0].name = localStorage.getItem('location-name');
                this.data[0].h = localStorage.getItem('location-h');
                this.selectedIndex = 0;
            }
            return
        },

        initData() {
            return [{lat:0, lon:0, h:0, name:""}];
        },

        reset() {
            this.query = "";
            this.selectedIndex = null;
            this.data = this.initData();
            this.open = false;
            this.focusedIndex = null;
        },

        async fetchLocations() {
            console.log(`query=${this.query}`);
            if (this.query.length == 0) {
                this.selectedIndex = null;
            }
            if (this.query.length < 3) {
                return null;
            };
            this.open = true;
            this.data = await getLocations(this.query);
            console.log(this.data);
        },

        closeListbox() {
            this.open = false;
            this.focusedIndex = null;
            this.search = '';
        },

        closeResults() {
            this.open = false;
            this.focusedIndex = null;
        },

        openResults() {
            this.open = true;
        },

        toggleResultsVisibility () {
            if (this.open) return this.closeResults();
            return this.openResults();
        },

        focusNextResult () {
            if (this.focusedIndex === null) {
                this.focusedIndex = 0;
                return
            }
            if (this.focusedIndex == this.data.length - 1) {
                // this.focusedIndex = null;
                return
            }
            return this.focusedIndex++;
        },

        focusPreviousResult() {
            // if (!this.focusedIndex) {
            //     this.focusedIndex = 0;
            //     return
            // }
            if (this.focusedIndex == 0 || this.focusedIndex === null) {
                this.focusedIndex = null;
                return
            }
            this.focusedIndex--;
            return
        },

        selectResult() {
            if (!this.open) return this.toggleResultsVisibility();
            this.selectedIndex = this.focusedIndex;
            this.query = this.data[this.selectedIndex].name;
            // Add selected query to localstorage
            localStorage.setItem('location-query', this.query);
            localStorage.setItem('location-lat', this.data[this.selectedIndex].lat);
            localStorage.setItem('location-lon', this.data[this.selectedIndex].lon);
            localStorage.setItem('location-name', this.data[this.selectedIndex].name);
            localStorage.setItem('location-h', this.data[this.selectedIndex].h);
            this.closeListbox();
        }
    }
};


export const setPassesFormListeners = (form) => {
    // select satellite id from previous search
    const satelliteSelect = document.querySelector("select[name=satid]");
    const prevSatId = localStorage.getItem("satid");
    if (prevSatId) {
        satelliteSelect.value = prevSatId;
    };
    form.addEventListener("submit", () => {
        const satname = satelliteSelect.options[satelliteSelect.selectedIndex].text;
        form.satname.value = satname
        localStorage.setItem("satid", satelliteSelect.value);
    });
};


export const setPassListListener = (passList) => {
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
        .then((resp) => showPassList(passList, resp, name))
        .catch(error => {
            console.error('Error getting passes: ' + error.message);
            showErrorMessage();
        });
};


const showPassList = (passListElement, resp, locationName) => {
    if (resp.overpasses.length == 0) {
        passList.innerHTML = `
            <p class="is-size-5 has-text-centered mt-6">
                No passes found
            </p>
        `
    }
    else {
        passListElement.innerHTML = "";
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
            passRowDiv.innerHTML = `
                <div class="p-1 pass-item pass-month-day">
                    <p class="value">${start_pt.getMonthDay}</p>
                </div>
                <div class="p-1 pass-item pass-time">
                    <p class="value">${start_pt.getTimeMinutes}</p>
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
            passListElement.appendChild(passRowDiv);
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


const filterVisibleOnlyPasses = (visibleOnly, passes) => {
    let filteredPasses;
    if (visibleOnly) {
        filteredPasses = passes.filter((pass) => pass.type == "visible");
    } else {
        filteredPasses = passes;
    }
    return filteredPasses;
};