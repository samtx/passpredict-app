import Autocomplete from './autocomplete.js';
import PassList from './PassList.svelte';
import HomeForm from './HomeForm.svelte';


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


const regExpEscape = (s) => {
    // From https://github.com/elcobvg/svelte-autocomplete/blob/master/src/index.html
    return s.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&")
}


export { Autocomplete, PassList, HomeForm, regExpEscape };