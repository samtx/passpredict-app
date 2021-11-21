export default (config) => {
    let ac = {
        query: "",
        results: [],
        selectedIndex: null,
        focusedIndex: null,
        open: false,

        // default config
        threshold: 3,

        async searchFunction(q) {
            return []
        },

        init() {
            return
        },

        reset() {
            this.query = "";
            this.selectedIndex = null;
            this.results = [];
            this.open = false;
            this.focusedIndex = null;
        },

        search() {
            console.log(`query=${this.query}`);
            if (this.query.length == 0) {
                this.selectedIndex = null;
            }
            if (this.query.length < this.threshold) {
                return null;
            };
            this.open = true;
            this.searchFunction(this.query).then(results => this.results = results );
            console.log(this.results);
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
            if (this.focusedIndex == this.results.length - 1) {
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
            this.query = this.results[this.selectedIndex].name;
            // Add selected query to localstorage
            localStorage.setItem('location-query', this.query);
            localStorage.setItem('location-lat', this.getValue('lat'));
            localStorage.setItem('location-lon', this.getValue('lon'));
            localStorage.setItem('location-name', this.getValue('name'));
            localStorage.setItem('location-h', this.getValue('h'));
            this.closeListbox();
        },

        getValue(key) {
            if (this.selectedIndex == null) {
                return "";
            }
            return this.results[this.selectedIndex][key];
        },

        getValueFixed(key, n = 0) {
            const value = this.getValue(key);
            const valueFixed = value === "" ? "" : parseFloat(value).toFixed(n);
            return valueFixed;
        },
    };

    // Initialize configuration
    if (config) {
        ac = Object.assign(ac, config);
    }
    return ac;
}