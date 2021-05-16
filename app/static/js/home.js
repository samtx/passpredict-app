// home.js

// import autoComplete from "@tarekraafat/autocomplete.js";

let selectedLocation;
let selectedSatId;

const Satellite = class {
    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
};

async function queryLocationAPI(search_text) {
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
    const locations = await queryLocationAPI(keyword);
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

window.locationSearch = function() {
    // For the location search autocomplete input alpine.js component
    return {
        query: "",
        data: [{lat:0, lon:0, h:0, name:""}],
        selectedIndex: 0,
        async fetchLocations() {
            console.log(`query=${this.query}`);
            const locations = await queryLocationAPI(this.query);
            const parsedLocations = parseLocations(locations);
            this.data = parsedLocations;
            console.table(this.data);
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    form.addEventListener('sumbit', function (e) {
        // modify form to send latitude and longitude

    });

    const locationInput = document.getElementById('locationSearch');
    const locationSuggestions = document.getElementById('locationSuggestions');
    locationInput.addEventListener('input', async function (evt) {
        // https://tarekraafat.github.io/autoComplete.js/#/usage?id=demo

        // new autoComplete({
        //     selector: "#locationSearch",
        //     data: {
        //         src: getLocations(),
        //         key: ["name"],
        //         cache: true,
        //     },
        //     resultItem: {
        //         highlight: {
        //             render: true
        //         }
        //     }

        // })

        // // https://tarekraafat.github.io/autoComplete.js/#/configuration?id=data-required

        // // data: {
        // // },


        // let inputText = evt.target.value;
        // let emptyArray = [];
        // if (inputText && inputText.length > 3) {
        //     results = await getLocations(inputText);

        // };

    })
});