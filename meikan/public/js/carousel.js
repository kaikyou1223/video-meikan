/**
 * 軽量カルーセル（イベントデリゲーション: 動的追加カードにも対応）
 */
(function () {
    'use strict';

    function getCarousel(el) {
        return el.closest('[data-carousel]');
    }

    function getSlides(carousel) {
        return carousel.querySelector('.work-card-v2__slides');
    }

    function getSlideWidth(slides) {
        var slide = slides.querySelector('.work-card-v2__slide');
        return slide ? slide.offsetWidth : 0;
    }

    function getCurrentIndex(slides) {
        var w = getSlideWidth(slides);
        return w > 0 ? Math.round(slides.scrollLeft / w) : 0;
    }

    function updateDots(carousel, index) {
        var dots = carousel.querySelectorAll('[data-carousel-dot]');
        dots.forEach(function (dot) {
            dot.classList.toggle('is-active', parseInt(dot.dataset.carouselDot, 10) === index);
        });
    }

    // 前へ
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-carousel-prev]');
        if (!btn) return;
        e.preventDefault();
        var carousel = getCarousel(btn);
        if (!carousel) return;
        var slides = getSlides(carousel);
        var w = getSlideWidth(slides);
        slides.scrollBy({ left: -w, behavior: 'smooth' });
    });

    // 次へ
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-carousel-next]');
        if (!btn) return;
        e.preventDefault();
        var carousel = getCarousel(btn);
        if (!carousel) return;
        var slides = getSlides(carousel);
        var w = getSlideWidth(slides);
        slides.scrollBy({ left: w, behavior: 'smooth' });
    });

    // ドットクリック
    document.addEventListener('click', function (e) {
        var dot = e.target.closest('[data-carousel-dot]');
        if (!dot) return;
        var carousel = getCarousel(dot);
        if (!carousel) return;
        var slides = getSlides(carousel);
        var w = getSlideWidth(slides);
        var index = parseInt(dot.dataset.carouselDot, 10);
        slides.scrollTo({ left: w * index, behavior: 'smooth' });
    });

    // 動画iframe: スライド幅に合わせてスケーリング
    function scaleVideoIframes() {
        document.querySelectorAll('.work-card-v2__slide--video').forEach(function (slide) {
            var iframe = slide.querySelector('.work-card-v2__video-iframe');
            if (!iframe) return;
            var slideWidth = slide.offsetWidth;
            if (slideWidth <= 0) return;
            var scale = slideWidth / 720;
            iframe.style.transform = 'scale(' + scale + ')';
            slide.style.height = Math.round(480 * scale) + 'px';
        });
    }
    // 初期化 + リサイズ対応
    scaleVideoIframes();
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(scaleVideoIframes, 150);
    });
    // 動的追加カード用: MutationObserverで検知
    new MutationObserver(function () { setTimeout(scaleVideoIframes, 50); })
        .observe(document.body, { childList: true, subtree: true });

    // スクロールでドット更新（デバウンス付き）
    var scrollTimers = new WeakMap();
    document.addEventListener('scroll', function (e) {
        var slides = e.target;
        if (!slides.classList || !slides.classList.contains('work-card-v2__slides')) return;
        var carousel = getCarousel(slides);
        if (!carousel) return;

        var timer = scrollTimers.get(slides);
        if (timer) clearTimeout(timer);
        scrollTimers.set(slides, setTimeout(function () {
            updateDots(carousel, getCurrentIndex(slides));
        }, 100));
    }, true);
})();
