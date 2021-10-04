// home.js

import { getLocations, markQuerySubstring } from './passpredictlib.js';

console.log('alright then')

// For the location search autocomplete input alpine.js component
window.markQuerySubstring = markQuerySubstring;

window.locationSearch = function() {
    return {
        query: "",
        data: [{lat:0, lon:0, h:0, name:""}],
        selectedIndex: 0,
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
            }
            return
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
}

document.addEventListener('DOMContentLoaded', () => {
    // select satellite id from previous search
    const satelliteSelect = document.querySelector("select[name=satid]");
    const prevSatId = localStorage.getItem("satid");
    if (prevSatId) {
        satelliteSelect.value = prevSatId;
    };
    // save satellite selection for next time
    const form = document.getElementById("passes-form");
    form.addEventListener("submit", () => {
        const satname = satelliteSelect.options[satelliteSelect.selectedIndex].text;
        form.satname.value = satname
        localStorage.setItem("satid", satelliteSelect.value);
    });
});