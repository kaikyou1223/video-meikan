<?php $headingText = '著者について'; require TEMPLATE_DIR . '/partials/section-heading.php'; ?>

<div class="author-profile">
    <div class="author-profile__header">
        <div class="author-profile__avatar"><picture><source srcset="<?= h(url('public/images/author-avatar.webp')) ?>" type="image/webp"><img src="<?= h(url('public/images/author-avatar.png')) ?>" alt="av博士" width="72" height="72" loading="lazy"></picture></div>
        <div class="author-profile__main">
            <h1 class="author-profile__name">av博士</h1>
            <p class="author-profile__tagline">月1万課金が止められない独身AVオタク</p>
        </div>
    </div>

    <div class="author-profile__body">
        <h2 class="author-profile__section-title">何者？</h2>
        <p>品番を言われれば0.5秒で作品が浮かぶ。年間500本以上見続けた結果、そういう脳になってしまった。どうも、av博士です。</p>

        <p>都内でひとり暮らしをしている30代の会社員だ。彼女はいない。仕事から帰ってきて、風呂入って、ビール片手にFANZAを開く。この流れが崩れると逆に体調を崩す。たぶん。</p>

        <p>気づけば毎月1万円以上をAVに注ぎ込むようになり、視聴本数は年間500本を余裕で超えた。友達に「お前それもう研究だろ」と言われたので、じゃあ博士を名乗ろうと。そんな軽いノリでこのサイトが生まれた。</p>

        <h2 class="author-profile__section-title">こんな目線で見てます</h2>
        <p>女優のエロさをスペックで語るのが好きじゃない。B88・W58と書いても、どんな体験になるかは伝わらない。だから自分が書くときは必ず「どのジャンルで見るべきか」を軸にしている。巨乳なら巨乳×どのプレイで映えるか。感度が高いなら、どの体位でそれが出るか。おかずを選ぶ情報として機能しないなら書く意味がないと思ってる。</p>

        <h2 class="author-profile__section-title">こんな特技があります</h2>
        <ul class="author-profile__list">
            <li><strong>品番を言われればどの作品か即答できる。</strong>「SSIS-834」って言われたら「三上悠亜のラスト作品」と0.5秒で返せる。飲み会で披露しても誰も喜ばなかった。</li>
            <li><strong>サムネイルだけで地雷作品を回避できる。</strong>長年の経験で培ったハズレセンサーが発動する。的中率は体感8割くらいで、残り2割は勉強代だと思っている。実際このセンサーでかなりの金を節約してきた。</li>
            <li><strong>素人モノでも出演女優が分かる。</strong>体のライン・仕草・声で判別できる。友人には「その能力もっと別のことに使え」と言われた。正論だと思う。</li>
            <li><strong>女優の移籍先を高確率で予想できる。</strong>SNSの動きとか撮影スタジオの写り込みとかで推測するんだが、これに関しては我ながらキモいと思っている。</li>
        </ul>

        <h2 class="author-profile__section-title">なんでこのサイト作ったの？</h2>
        <p>きっかけは「三上悠亜のNTR作品だけまとめて見たいのに、探すのがめんどくさすぎる」という極めて個人的な不満だった。</p>

        <p>同じ女優でもジャンルが違うとまるで別人になる。清楚系の女優がNTRに出ると破壊力が上がるし、ギャル系が人妻モノに出るとギャップで脳がバグる。この「女優×ジャンル」の組み合わせこそが至高なのに、それをサクッと探せるサイトがなかった。じゃあ自分で作るか、と。誰にも頼まれてないのに勝手に作った。</p>

        <p>正直、自分が使いたくて作ったサイトだ。その目的は叶っているので個人的には満足している。同じ欲求を持つ人間がいれば、ついでに役立つかもしれない。</p>

        <h2 class="author-profile__section-title">好きなジャンル</h2>
        <div class="author-profile__tags">
            <span class="author-profile__tag">NTR</span>
            <span class="author-profile__tag">人妻</span>
            <span class="author-profile__tag">痴女</span>
            <span class="author-profile__tag">巨乳</span>
            <span class="author-profile__tag">お姉さん</span>
        </div>
        <p>NTRは人類が生み出した最高のフィクションだと思っている。異論は認める。痴女は「自分を選んでくれる」というファンタジーが機能する稀有なジャンルで、人妻モノはバックストーリーが仕事の半分以上をしている。</p>

        <h2 class="author-profile__section-title">毎月どれくらい使ってるの？</h2>
        <ul class="author-profile__list">
            <li>単品購入（新作チェック用）：5,000〜8,000円</li>
            <li>見放題プラン：約3,000円</li>
            <li>深夜のテンションで買う衝動買い：2,000〜3,000円</li>
        </ul>
        <p>合計すると月1万〜1.5万円くらい。飲み会2回分だと思えば安い。安くないか。まあ飲み会より確実に満足度は高いので良しとしている。</p>

        <p>一番後悔した買い物は、酔った勢いで買った10本セットの福袋だ。7本くらいハズレだった。福袋は買うな。</p>
    </div>
</div>

<?php $headingText = '最新記事'; require TEMPLATE_DIR . '/partials/section-heading.php'; ?>
<div class="article-list">
    <?php foreach (array_slice($articles, 0, 6) as $article): ?>
    <a href="<?= h(url('article/' . $article['slug'] . '/')) ?>" class="article-list-card">
        <div class="article-list-card__body">
            <?php if (!empty($article['category'])): ?>
            <span class="article-list-card__category"><?= h($article['category']) ?></span>
            <?php endif; ?>
            <h2 class="article-list-card__title"><?= h($article['title']) ?></h2>
            <time class="article-list-card__date"><?= h($article['published_at']) ?></time>
        </div>
    </a>
    <?php endforeach; ?>
</div>
