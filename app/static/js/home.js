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
            // this.$watch('query', ((query_str) => {
            //     if (!this.open || query_str < 3) return
            // }))
            return
        },

        async fetchLocations() {
            console.log(`query=${this.query}`);
            if (this.query.length < 3) return null
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
            this.closeListbox();
        }
    }
}
