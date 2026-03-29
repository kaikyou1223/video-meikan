// Hamburger Menu
document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.header__hamburger');
    var nav = document.getElementById('globalNav');
    if (!btn || !nav) return;

    btn.addEventListener('click', function () {
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        nav.classList.toggle('is-open');
    });
});

// Cast Table: もっと見る / 閉じる
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.cast-table-collapsible').forEach(function (wrap) {
        var btn = wrap.querySelector('.cast-table__toggle');
        if (!btn) return;
        btn.addEventListener('click', function () {
            wrap.classList.toggle('is-open');
        });
    });
});
