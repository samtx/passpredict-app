// module for passpredict javascript functions

class Point {
    constructor(obj) {
        this.date = new Date(obj.datetime);  // datetime string
        this.azimuth = obj.azimuth;
        this.elevation = obj.elevation;
        this.range = obj.range;
        this.brightness = obj.brightness;
    }

    get getMonthDay() {
        const d = new Intl.DateTimeFormat([], { dateStyle: "short" }).format(this.date);
        const dateString = d.split("/").slice(0, 2).join("/");
        return dateString;
    }

    get getTimeMinutes() {
        const t = new Intl.DateTimeFormat([], { timeStyle: "short" }).format(this.date);
        return t;
    }

    get getTime() {
        const t = new Intl.DateTimeFormat([], { timeStyle: "medium" }).format(this.date);
        return t;
    }
}


// class Pass {
//     constructor(obj) {
//         this.start_pt = obj.start_pt;
//         this.max_pt = obj.max_pt;
//         this.end_pt = obj.end_pt;
//         this.type = obj.type;
//         this.brightness = obj.brightness;
//     }
// }


const getPassQuality = (pass) => {
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

async function searchLocation(search_text) {
    const params = {
        access_token: MAPBOX_ACCESS_TOKEN,
        autocomplete: true,
        types: [
            "postcode",
            "district",
            "place",
            "locality",
            "neighborhood",
            "address",
        ],
    };
    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURI(
        search_text
    )}.json`;
    const response = await fetch(
        url + "?" + new URLSearchParams(params).toString()
    );
    const json = await response.json();
    const { features: locations } = json;
    return locations;
}

const parseLocations = (locations) => {
    console.log(locations);
    locations = locations.map((locationObject) => {
        const {
            place_name: name,
            geometry: { coordinates: lonlat },
        } = locationObject;
        return {
            name: name,
            lat: lonlat[1],
            lon: lonlat[0], // switch the order to lat, lon
        };
    });
    console.log(locations);
    return locations;
};

const getLocations = async (keyword) => {
    console.log(`keyword=${keyword}`);
    const locations = await searchLocation(keyword);
    const parsedLocations = parseLocations(locations);
    return parsedLocations;
};

export {Point, getLocations, parseLocations, searchLocation, getPassQuality}