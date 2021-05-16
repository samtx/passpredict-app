// home.js

import { getLocations } from './passpredictlib.js';

let selectedLocation;
let selectedSatId;

const Satellite = class {
    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
};

const goToPasses = (event) => {
    // get satellite name
    const sel = document.querySelector("select[name=satid]");
    const satname = sel.options[sel.selectedIndex].text;

    const params = {
        name: selectedLocation.name,
        lat: selectedLocation.lat,
        lon: selectedLocation.lon,
        satname: satname,
    };
    const url =
        `/passes/${selectedSatId}?` +
        new URLSearchParams(params).toString();
    router.goto(url);
};

// For the location search autocomplete input alpine.js component
window.locationSearch = function() {
    return {
        query: "",
        data: [{lat:0, lon:0, h:0, name:""}],
        selectedIndex: 0,
        async fetchLocations() {
            console.log(`query=${this.query}`);
            if (this.query.length < 3) return null
            this.data = await getLocations(this.query);
            console.table(this.data);
        }
    }
}
