
// medium zoom
window.onload = function () {
    mediumZoom('img[alt="Patch Image"]', {
        margin: 0,
        background: "rgba(0, 0, 0, .8)",
    });
};

// tooltip bootstrap
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});