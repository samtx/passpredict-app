// home.js

import { getLocations, markQuerySubstring } from './passpredictlib.js';

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
window.markQuerySubstring = markQuerySubstring;

window.locationSearch = function() {
    return {
        query: "",

        data: [{lat:0, lon:0, h:0, name:""}],

        selectedIndex: 0,

        focusedIndex: null,

        open: false,

        async fetchLocations() {
            console.log(`query=${this.query}`);
            if (this.query.length < 3) return null
            this.data = await getLocations(this.query);
            console.log(this.data);
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
            if (!this.focusedIndex) {
                this.focusedIndex = 0;
                return
            }
            if (this.focusedIndex == this.data.length - 1) {
                this.focusedIndex = null;
            }
            return this.focusedIndex++;
        },

        focusPreviousResult() {
            // if (!this.focusedIndex) {
            //     this.focusedIndex = 0;
            //     return
            // }
            if (this.focusedIndex == 0) {
                this.focusedIndex = null;
            }
            return this.focusedIndex--;
        },

        selectResult() {
            if (!this.open) return this.toggleResultsVisibility();
            this.selectedIndex = this.focusedIndex;
            this.query = this.data[this.selectedIndex].name;
        }


    }
}
