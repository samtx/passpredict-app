export default class Autocomplete {

    constructor(config) {
        this.query = "",
        this.data = [],
        this.selectedIndex = null,
        this.focusedIndex = null;
        this.open = false;
        this.threshold = ('threshold' in config) ? config.threshold : 3;
    }

    async fetchData(q) {}

    init() {
        // // check localstorage for previous search query
        // let query = localStorage.getItem('location-query');
        // if (query) {
        //     this.query = query;
        //     this.data[0].lat = localStorage.getItem('location-lat');
        //     this.data[0].lon = localStorage.getItem('location-lon');
        //     this.data[0].name = localStorage.getItem('location-name');
        //     this.data[0].h = localStorage.getItem('location-h');
        //     this.selectedIndex = 0;
        // }
        return
    }

    initData() {
        return [{lat:0, lon:0, h:0, name:""}];
    }

    reset() {
        this.query = "";
        this.selectedIndex = null;
        this.data = this.initData();
        this.open = false;
        this.focusedIndex = null;
    }

    fetch() {
        console.log(`query=${this.query}`);
        if (this.query.length == 0) {
            this.selectedIndex = null;
        }
        if (this.query.length < this.threshold) {
            return null;
        };
        this.openResults();
        this.fetchData(this.query).then(data => this.data = data);
        console.log(this.data);
    }

    closeListbox() {
        this.open = false;
        this.focusedIndex = null;
        this.search = '';
    }

    closeResults() {
        this.open = false;
        this.focusedIndex = null;
    }

    openResults() {
        this.open = true;
    }

    toggleResultsVisibility () {
        if (this.open) return this.closeResults();
        return this.openResults();
    }

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
    }

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
    }

    selectResult() {
        if (!this.open) return this.toggleResultsVisibility();
        this.selectedIndex = this.focusedIndex;
        this.query = this.data[this.selectedIndex].name;
        // Add selected query to localstorage
        localStorage.setItem('location-query', this.query);
        localStorage.setItem('location-lat', this.getValue('lat'));
        localStorage.setItem('location-lon', this.getValue('lon'));
        localStorage.setItem('location-name', this.getValue('name'));
        localStorage.setItem('location-h', this.getValue('h'));
        this.closeListbox();
    }

    getValue(key) {
        if (this.selectedIndex == null) {
            return "";
        }
        return this.data[this.selectedIndex][key];
    }

    getValueFixed(key, n = 0) {
        const value = this.getValue(key);
        const valueFixed = value === "" ? "" : parseFloat(value).toFixed(n);
        return valueFixed;
    }

};