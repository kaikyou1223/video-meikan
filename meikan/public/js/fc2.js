// FC2 ランキング: 投票・コピー
document.addEventListener('DOMContentLoaded', function () {

    // --- トースト ---
    var toastEl = null;
    var toastTimer = null;

    function showToast(message) {
        if (!toastEl) {
            toastEl = document.createElement('div');
            toastEl.className = 'fc2-toast';
            document.body.appendChild(toastEl);
        }
        toastEl.textContent = message;
        // reflow させて transition を効かせる
        void toastEl.offsetWidth;
        toastEl.classList.add('is-visible');

        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toastEl.classList.remove('is-visible');
        }, 1800);
    }

    // --- いいね（投票）---
    document.querySelectorAll('.fc2-vote-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (btn.disabled) return;

            var workId = btn.dataset.workId;
            if (!workId) return;

            btn.disabled = true;

            var formData = new FormData();
            formData.append('work_id', workId);

            fetch(BASE_URL + 'fc2/vote/', {
                method: 'POST',
                body: formData,
            })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    // 票数を親カードの表示に反映
                    var card = btn.closest('.fc2-work-card');
                    var countEl = card && card.querySelector('.fc2-work-card__vote-count');
                    if (countEl) countEl.textContent = data.vote_count + '票';

                    if (data.success || data.already) {
                        btn.classList.add('is-voted');
                    } else {
                        btn.disabled = false;
                    }
                })
                .catch(function () {
                    btn.disabled = false;
                });
        });
    });

    // --- コピー ---
    document.querySelectorAll('.fc2-copy-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var cid = btn.dataset.cid;
            if (!cid) return;

            navigator.clipboard.writeText(cid).then(function () {
                btn.classList.add('is-copied');
                btn.title = 'コピーしました';
                showToast('クリップボードにコピーしました！');
                setTimeout(function () {
                    btn.classList.remove('is-copied');
                    btn.title = '番号をコピー';
                }, 1500);
            });
        });
    });
});
