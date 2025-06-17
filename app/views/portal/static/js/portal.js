document.addEventListener('DOMContentLoaded', function () {
    get_user_stats();
    setupListeners();
});

function get_user_stats() {
    const incident_count = document.querySelector('#incident-count');
    const request_count = document.querySelector('#request-count');
    const idea_count = document.querySelector('#idea-count');
    const device_count = document.querySelector('#device-count');

    fetch('/api/get_user_stats/').then(function (response) {
        response.json().then(function (data) {
            incident_count.innerHTML = data.incidents
            request_count.innerHTML = data.requests
            idea_count.innerHTML = data.ideas
            device_count.innerHTML = data.ideas
        });
    });
};


async function validate_Help_Form() {
    const short_desc = document.getElementById('short_desc')
    const details = document.getElementById('details')

    if (short_desc.value == '') {
        await showSwal('Error', 'Please provide a short description', 'error');

        return false
    } else {
        await showSwal(
            'Success',
            'Your support ticket has been logged. Someone will contact you shortly to help with your issue',
            'success');
    }
};

async function updateCarousel() {
    const carouselInner = document.querySelector('#announcement-carousel .carousel-inner');

    const response = await fetch('/api/get_active_announcements/')
    const data = await response.json()
    if (data) {
        // Clear previous content
        carouselInner.innerHTML = '';

        // Add announcements to the carousel
        data.forEach((announcement, index) => {
            const item = document.createElement('div');
            if (index === 0) {
                item.classList.add('active');
            }

            item.classList.add('carousel-item');
            carouselInner.appendChild(item);

            item.addEventListener('dblclick', async () => {
                // Trigger the popover
                await showSwal(announcement.title, `
                            <p>${announcement.announcement}</p>
                            <p>Start: ${announcement.start}</p>
                        `,
                    'info');
            });

            const caption = document.createElement('div');
            caption.classList.add('carousel-caption');
            caption.innerHTML = `
                <div>
                  <h5>${announcement.title}</h5>
                  <small>Posted: ${announcement.start}</small>
                  <p>${announcement.announcement}</p>
                </div>
              `;
            item.appendChild(caption);
        });

    } else {
        // If no announcements, display a default image
        const defaultItem = document.createElement('div');
        defaultItem.classList.add('carousel-item', 'active');  // Add 'active' class to the default item
        carouselInner.appendChild(defaultItem);  // Append defaultItem instead of item

        const caption = document.createElement('div');
        caption.classList.add('carousel-caption');
        caption.innerHTML = `
        <div>
            <h5>No Current Issues</h5>
            <p>We will announce them here if anything comes up</p>
            <p>(well more like "goes down" but you get the point</p>
        </div>
    `;
        defaultItem.appendChild(caption);
    }
}

function setupListeners() {
    document.getElementById("get-help-btn").addEventListener("click", () => {
        window.location.href = "/portal/my-tickets/?active_tab=support";
    });


}

// Initial update and set interval for periodic updates
updateCarousel();
setInterval(updateCarousel, 60000); // Update every minute (adjust as needed)