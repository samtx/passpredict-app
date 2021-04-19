// module for passpredict javascript functions

let selectedLocation;
let selectedSatId;

const Satellite = class {
    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
};

let satellites = [
    new Satellite(25544, "International Space Station"),
    new Satellite(20580, "Hubble Space Telescope"),
    new Satellite(25338, "NOAA-15"),
    new Satellite(28654, "NOAA-18"),
    new Satellite(33591, "NOAA-19"),
    new Satellite(44420, "Lightsail 2"),
    new Satellite(29155, "GOES 13"),
    new Satellite(25994, "TERRA"),
    new Satellite(40069, "METEOR M2"),
];

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