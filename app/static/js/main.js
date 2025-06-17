import {getCurrentUser} from './includes/utils.js';
import {userProfileClass} from './includes/user-profile-class.js';
import {showFormButtons, showSwal} from './includes/form-classes/form-utils.js';
import {UserAvatarClass} from './includes/user-avatar-class.js';
import {enableToolTips} from './includes/form-classes/form-utils.js';
import {sunEditorClass} from './includes/suneditor-class.js';

document.addEventListener('DOMContentLoaded', async function () {
    // disable right click in production
    // document.addEventListener('contextmenu', event => event.preventDefault());

    fullScreenToggle();
    userProfileClass.init();

    // functions for modals that prevent aria warnings
    modalCloseListener();

    await setHeaderUserAvatar();
    const userAvatarClass = new UserAvatarClass();
    userAvatarClass.init();

    enableToolTips()
    sidebar();
});


async function setHeaderUserAvatar() {
    const headerUserAvatar = document.getElementById('header-user-avatar');
    if (!headerUserAvatar) return;

    const currentUser = await getCurrentUser();
    if (currentUser?.avatar) {
        headerUserAvatar.src = currentUser.avatar;
    }
}

function fullScreenToggle() {
    const fs_toggle = document.getElementById('fs-toggle');
    if (fs_toggle) {
        fs_toggle.addEventListener('click', function () {
            if (!document.fullscreenElement && !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
                // Enter fullscreen
                fs_toggle.classList = 'bi bi-fullscreen-exit fullscreen-button';
                if (document.documentElement.requestFullscreen) {
                    document.documentElement.requestFullscreen();
                } else if (document.documentElement.mozRequestFullScreen) { // Firefox
                    document.documentElement.mozRequestFullScreen();
                } else if (document.documentElement.webkitRequestFullscreen) { // Chrome, Safari, and Opera
                    document.documentElement.webkitRequestFullscreen();
                } else if (document.documentElement.msRequestFullscreen) { // IE/Edge
                    document.documentElement.msRequestFullscreen();
                }
            } else {
                // Exit fullscreen
                fs_toggle.classList = 'bi bi-arrows-fullscreen fullscreen-button';
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.mozCancelFullScreen) { // Firefox
                    document.mozCancelFullScreen();
                } else if (document.webkitExitFullscreen) { // Chrome, Safari, and Opera
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) { // IE/Edge
                    document.msExitFullscreen();
                }
            }
        });
    }
};


function modalCloseListener() {
    document.addEventListener('hide.bs.modal', function (event) {
        const modal = event.target;

        // Handle regular focused elements
        const focused = document.activeElement;
        if (modal.contains(focused)) {
            // Add the inert attribute to the modal
            modal.setAttribute('inert', '');

            // Move focus to the modal trigger or any other focusable element
            const modalTrigger = document.querySelector(`[data-bs-target="#${modal.id}"]`);
            if (modalTrigger) {
                modalTrigger.focus();
            } else {
                // If there's no modal trigger, move focus to the body or any other focusable element
                document.body.focus();
            }

            // Remove the inert attribute from the modal after the transition is complete
            setTimeout(() => {
                modal.removeAttribute('inert');
            }, 300); // Bootstrap modal transition duration
        }
    });
}

function sidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Toggle sidebar on mobile
    function toggleSidebar() {
        sidebar.classList.toggle('show');
        sidebarOverlay.classList.toggle('show');
        document.body.classList.toggle('sidebar-open');
    }

    // Close sidebar
    function closeSidebar() {
        sidebar.classList.remove('show');
        sidebarOverlay.classList.remove('show');
        document.body.classList.remove('sidebar-open');
    }

    // Event listeners
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Close sidebar when clicking nav links on mobile
    const navLinks = sidebar.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });

    // Optional: Keyboard support (ESC to close)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            closeSidebar();
        }
    });
}



