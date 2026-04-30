/**
 * 広告スロットの遅延ロード
 *
 * <div class="ad-slot" data-ad-lazy="1">
 *   <div class="ad-slot__inner">
 *     <template class="ad-slot__lazy-template">
 *       <ins .../><script .../>
 *     </template>
 *   </div>
 * </div>
 *
 * IntersectionObserver で viewport 接近時に template の中身を展開し、
 * <script> を再生成して実行させる。
 */
(function () {
    'use strict';

    function activate(slot) {
        if (slot.dataset.adActivated) return;
        slot.dataset.adActivated = '1';

        var templates = slot.querySelectorAll('.ad-slot__inner > template.ad-slot__lazy-template');
        templates.forEach(function (tpl) {
            var inner = tpl.parentElement;
            // 非表示の inner はロード不要（SP/PC切替の対岸）
            if (window.getComputedStyle(inner).display === 'none') return;

            var frag = tpl.content.cloneNode(true);
            // <script> はそのまま innerHTML 経由では実行されないので、再生成して入れ替える
            frag.querySelectorAll('script').forEach(function (oldScript) {
                var newScript = document.createElement('script');
                for (var i = 0; i < oldScript.attributes.length; i++) {
                    var a = oldScript.attributes[i];
                    newScript.setAttribute(a.name, a.value);
                }
                if (oldScript.textContent) newScript.textContent = oldScript.textContent;
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });
            inner.appendChild(frag);
            tpl.remove();
        });
    }

    var observer = null;
    if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    activate(e.target);
                    observer.unobserve(e.target);
                }
            });
        }, { rootMargin: '300px' });
    }

    function init(root) {
        var scope = root || document;
        var slots = scope.querySelectorAll('[data-ad-lazy="1"]:not([data-ad-activated])');
        slots.forEach(function (slot) {
            if (observer) {
                observer.observe(slot);
            } else {
                // フォールバック: IO 非対応ブラウザは即時ロード
                activate(slot);
            }
        });
    }

    init();
    // 無限スクロールで追加された広告にも適用できるよう公開
    window.adsLazyInit = init;
})();
