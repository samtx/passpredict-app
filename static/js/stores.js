import { writable } from 'svelte/store';

export const location = writable({name:'', lat:0, lon:0, h:0});