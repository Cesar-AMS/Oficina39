(function () {
    function onReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
            return;
        }
        fn();
    }

    onReady(function () {
        const toggle = document.getElementById('menuToggle');
        const sidebar = document.querySelector('.menu-lateral');
        const overlay = document.getElementById('menuOverlay');

        if (!toggle || !sidebar || !overlay) return;

        function setOpen(open) {
            sidebar.classList.toggle('is-open', open);
            overlay.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            document.body.classList.toggle('menu-open', open);
        }

        toggle.addEventListener('click', function () {
            setOpen(!sidebar.classList.contains('is-open'));
        });

        overlay.addEventListener('click', function () {
            setOpen(false);
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth > 768) {
                setOpen(false);
            }
        });
    });
})();
