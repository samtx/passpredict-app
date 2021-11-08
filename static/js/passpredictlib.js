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