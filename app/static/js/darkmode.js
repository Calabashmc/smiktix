/**
 *  Light Switch @version v0.1.4
 */

(function () {
    const lightSwitch = document.querySelector('#lightSwitch');
    if (!lightSwitch) {
        return;
    }

    /**
     * @function darkmode
     * @summary: changes the theme to 'dark mode' and save settings to local storage.
     * Basically, replaces/toggles every CSS class that has '-light' class with '-dark'
     */
    function darkMode() {
        document.querySelectorAll('.bg-light').forEach((element) => {
            element.className = element.className.replace(/-light/g, '-dark');
        });

        const htmlTag = document.documentElement;
        if (htmlTag.getAttribute("data-bs-theme") !== "dark") {
            htmlTag.setAttribute("data-bs-theme", "dark");
        }
        document.body.classList.add('bg-dark');

        if (document.body.classList.contains('text-dark')) {
            document.body.classList.replace('text-dark', 'text-light');
        } else {
            document.body.classList.add('text-light');
        }

        // Tables
        const tables = document.querySelectorAll('table');
        for (let i = 0; i < tables.length; i++) {
            // add table-dark class to each table
            tables[i].classList.add('table-dark');
        }

        // set light switch input to true
        if (!lightSwitch.checked) {
            lightSwitch.checked = true;
        }
        localStorage.setItem('lightmode', 'dark');
    }

    /**
     * @function lightmode
     * @summary: changes the theme to 'light mode' and save settings to local storage.
     */
    function lightMode() {
        document.querySelectorAll('.bg-dark').forEach((element) => {
            element.className = element.className.replace(/-dark/g, '-light');
        });

        const htmlTag = document.documentElement;
        if (htmlTag.getAttribute("data-bs-theme") === "dark") {
            htmlTag.removeAttribute("data-bs-theme");
        }

        document.body.classList.add('bg-light');

        if (document.body.classList.contains('text-light')) {
            document.body.classList.replace('text-light', 'text-dark');
        } else {
            document.body.classList.add('text-dark');
        }

        // Tables
        const tables = document.querySelectorAll('table');
        for (let i = 0; i < tables.length; i++) {
            if (tables[i].classList.contains('table-dark')) {
                tables[i].classList.remove('table-dark');
            }
        }


        if (lightSwitch.checked) {
            lightSwitch.checked = false;
        }
        localStorage.setItem('lightmode', 'light');
    }

    /**
     * @function onToggleMode
     * @summary: the event handler attached to the switch. calling @darkMode or @lightMode depending on the checked state.
     */
    function onToggleMode() {
        const mode_btn = document.getElementById('mode-btn');
        const mode_icon = document.getElementById('mode-icon');
        const sun = document.querySelector("#sun");
        const moon = document.querySelector("#moon");

        if (lightSwitch.checked) {
            darkMode();
            mode_btn.classList.remove('btn-light');
            mode_btn.classList.add('btn-dark');
            sun.style.display = "none";
            moon.style.display = "block"
        } else {
            lightMode();
            mode_btn.classList.remove('btn-dark');
            mode_btn.classList.add('btn-light');
            sun.style.display = "block"
            moon.style.display = "none"
        }
    }


    /**
     * @function getSystemDefaultTheme
     * @summary: get system default theme by media query
     */
    function getSystemDefaultTheme() {
        const darkThemeMq = window.matchMedia('(prefers-color-scheme: dark)');
        if (darkThemeMq.matches) {
            return 'dark';
        }
        return 'light';
    }

    function setup() {
        let settings = localStorage.getItem('lightmode');
        if (settings == null) {
            settings = getSystemDefaultTheme();
        }

        if (settings === 'dark') {
            lightSwitch.checked = true;
        }

        lightSwitch.addEventListener('change', onToggleMode);

        onToggleMode();
    }
    setup();
})();

