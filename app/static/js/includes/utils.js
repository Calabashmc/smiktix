export async function getCurrentUser() {
    let response = await fetch('/api/people/get-current-user');
    return await response.json();
}

// This was originally in the ChangeWindow class from change-window.js as that is the only place sliders are
// now used. But need to use this to set restore point if form change is cancelled so moved out of the class as
// a utility function. This will also facilitate adding sliders to other pages if needed in future releases.
export function setSliderInitial(slider, label, trackColor) {
    const scale = (num, in_min, in_max, out_min, out_max) => {
        return ((num - in_min) * (out_max - out_min)) / (in_max - in_min) + out_min;
    };

    const value = Number(slider.value)
    const colorValue = (value - slider.min) / (slider.max - slider.min) * 100;
    slider.style.background = `linear-gradient(to right, ${trackColor} 0%, ${trackColor} ${colorValue}%, #ccc ${colorValue}%, #ccc 100%)`;

    const range_width = getComputedStyle(slider).getPropertyValue('width');
    const label_width = getComputedStyle(label).getPropertyValue('width');
    const num_width = +range_width.substring(0, range_width.length - 2);
    const num_label_width = +label_width.substring(0, label_width.length - 2);
    const max = slider.max;
    const min = slider.min;
    // Calculate the left value
    const left = value * (num_width / max) - num_label_width / 2 + scale(value, min, max, 10, -10);

    label.style.left = `${left}px`;
    label.innerHTML = value.toFixed(1);
}