
import Autocomplete from './autocomplete.js';

console.log('alright then')

// window.Alpine = Alpine;


const setNavbarMenuListener = () => {
    // Reference: https://bulma.io/documentation/components/navbar/#navbar-menu
    // Get all "navbar-burger" elements
    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    // Check if there are any navbar burgers
    if ($navbarBurgers.length > 0) {
        // Add a click event on each of them
        $navbarBurgers.forEach(el => {
            el.addEventListener('click', () => {
                // Get the target from the "data-target" attribute
                const target = el.dataset.target;
                const $target = document.getElementById(target);
                // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
                el.classList.toggle('is-active');
                $target.classList.toggle('is-active');
            });
        });
    }
}
setNavbarMenuListener();

// module for passpredict javascript functions

class Point {
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

class Pass {
    constructor(obj) {
        // Create javascript object from API JSON response
        this.start_pt = new Point(obj.aos);
        this.max_pt = new Point(obj.tca);
        this.end_pt = new Point(obj.los);
        this.total_seconds = obj.duration;
        this.type = obj.type;
        this.brightness = obj.brightness ? obj.brightness : "";
    }

    get quality() {
        if (this.type !== 'visible') { return 0 }
        if (this.max_pt.elevation > 70) { return 1 }
        if (this.max_pt.elevation > 45) { return 2 }
        if (this.max_pt.elevation > 10) { return 3 }
        return null
    }

    get duration() {
        // Return string of MM:SS
        const minutes = this.total_seconds / 60.0
        let seconds = this.total_seconds - Math.floor(minutes) * 60;
        seconds = seconds.toFixed(0);
        let seconds_str = padZeros(seconds, 2);
        let duration_string = `${minutes.toFixed(0)}:${seconds_str}`
        return duration_string;
    }

    get elevation() {
        // Return maximum elevation rounded to the nearest degree
        return Math.round(this.max_pt.elevation)
    }
}

const regExpEscape = (s) => {
    // From https://github.com/elcobvg/svelte-autocomplete/blob/master/src/index.html
    return s.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&")
}


const markQuerySubstring = (query, string) => {
    query = regExpEscape(query);
    string = string.replace(new RegExp(query, 'gmi'), `<strong>${query}</strong>`);
    return string
}

const padZeros = (n, size) => {
    let nstr = n.toString();
    while (nstr.length < size) {
        nstr = "0" + nstr;
    }
    return nstr
}


const setPassesFormListeners = (form) => {
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


export { Autocomplete, Pass, Point, regExpEscape, padZeros };