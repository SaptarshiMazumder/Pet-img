export type Lang = 'en' | 'ja';

export interface T {
  nav: {
    home: string;
    createPortrait: string;
    orders: string;
    myGenerations: string;
    signIn: string;
    signOut: string;
  };
  hero: {
    line1: string;
    accent: string;
    subtitle: string;
    cta: string;
  };
  create: {
    step1: string;
    step2: string;
    step3: string;
    dryRun: string;
    dryRunHint: string;
    generate: string;
    generateDry: string;
    submitting: string;
    orderPrint: string;
    generating: string;
  };
  gallery: {
    community: string;
    loading: string;
    noSamples: string;
    noSamplesHint: string;
  };
  styles: {
    seeAll: string;
    exploreStyles: string;
    selectStyle: string;
  };
  bottomBar: {
    home: string;
    create: string;
    orders: string;
    gallery: string;
  };

  queue: {
    view: string;
    tryAgain: string;
    failed: string;
    status: {
      pending: string;
      processing: string;
      fixing: string;
      completed: string;
      failed: string;
    };
  };
  past: {
    title: string;
    refresh: string;
    empty: string;
    deselect: string;
    selectForOrder: string;
    delete: string;
  };
  upload: {
    drop: string;
    hint: string;
    changePhoto: string;
  };
  orders: {
    title: string;
    refresh: string;
    empty: string;
    emptyHint: string;
    paid: string;
    unpaid: string;
    edit: string;
    payNow: string;
    processing: string;
    paidOn: string;
    deliveryMsg: string;
    emailSentTo: string;
  };
  orderFlow: {
    configurePrints: string;
    shipping: string;
    done: string;
    selectFrame: string;
    color: string;
    size: string;
    orientation: string;
    portrait: string;
    landscape: string;
    qty: string;
    total: string;
    cancel: string;
    shippingDetails: string;
    saving: string;
    back: string;
    payNow: string;
    processing: string;
    successMsg: string;
    successSub: string;
    close: string;
    viewOrders: string;
  };
  shipping: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address: string;
    addressPlaceholder: string;
    addressLine2Placeholder: string;
    city: string;
    postCode: string;
    country: string;
    saveDetails: string;
  };
  lightbox: {
    orderPrint: string;
  };
  footer: {
    support: string;
    privacy: string;
    terms: string;
    scta: string;
    brand: string;
  };
  confirm: {
    regenerate: string;
  };
  backToHome: string;
  auth: {
    signIn: string;
    signUp: string;
    email: string;
    password: string;
    forgotPassword: string;
    sendResetEmail: string;
    confirmPassword: string;
    passwordMismatch: string;
    resetSent: string;
    orContinueWith: string;
    noAccount: string;
    hasAccount: string;
    submitting: string;
  };
}

export const TRANSLATIONS: Record<Lang, T> = {
  en: {
    nav: {
      home: 'Home',
      createPortrait: 'Create Portrait',
      orders: 'Orders',
      myGenerations: 'My Generations',
      signIn: 'Sign in',
      signOut: 'Sign out',
    },
    hero: {
      line1: 'Transform your pet into',
      accent: 'Edo-era art',
      subtitle: 'Upload any photo and choose from our curated portrait styles inspired by Ukiyo-e masters.',
      cta: 'Create Portrait',
    },
    create: {
      step1: '1 · Upload your pet',
      step2: '2 · Select style',
      step3: '3 · Orientation',
      dryRun: 'Dry run',
      dryRunHint: '(print prompt, skip RunPod)',
      generate: 'Generate Portrait',
      generateDry: 'Generate (Dry Run)',
      submitting: 'Submitting…',
      orderPrint: 'Order Print',
      generating: 'Generating',
    },
    gallery: {
      community: 'Community',
      loading: 'Loading…',
      noSamples: 'No samples yet',
      noSamplesHint: 'Check back soon for Edo-era portrait examples',
    },
    styles: {
      seeAll: 'See All',
      exploreStyles: 'Explore Styles',
      selectStyle: 'Select Style',
    },
    bottomBar: {
      home: 'Home',
      create: 'Create',
      orders: 'Orders',
      gallery: 'Gallery',
    },
    queue: {
      view: 'View',
      tryAgain: '↺ Try again',
      failed: 'Generation failed',
      status: {
        pending: 'Queued',
        processing: 'Generating',
        fixing: 'Fixing',
        completed: 'Done',
        failed: 'Failed',
      },
    },
    past: {
      title: 'Select to order for print',
      refresh: 'Refresh',
      empty: 'No portraits yet — generate one above!',
      deselect: 'Deselect',
      selectForOrder: 'Select for order',
      delete: 'Delete',
    },
    upload: {
      drop: "Drop your pet's photo here",
      hint: 'PNG · JPG · WEBP  ·  or click to browse',
      changePhoto: 'Change photo',
    },
    orders: {
      title: 'Your Orders',
      refresh: 'Refresh',
      empty: 'No orders yet.',
      emptyHint: 'Select portraits from your gallery and tap "Order portraits" to get started.',
      paid: 'Paid',
      unpaid: 'Unpaid',
      edit: 'Edit',
      payNow: 'Pay Now',
      processing: 'Processing…',
      paidOn: 'Paid on',
      deliveryMsg: 'Your order has been placed and will be delivered within 10–14 days after payment confirmation.',
      emailSentTo: 'A confirmation email has been sent to',
    },
    orderFlow: {
      configurePrints: 'Configure prints',
      shipping: 'Shipping',
      done: 'Done',
      selectFrame: 'Select Frame',
      color: 'Color',
      size: 'Size',
      orientation: 'Orientation',
      portrait: 'Portrait',
      landscape: 'Landscape',
      qty: 'Qty',
      total: 'Total',
      cancel: 'Cancel',
      shippingDetails: 'Shipping details',
      saving: 'Saving…',
      back: '← Back',
      payNow: 'Pay Now',
      processing: 'Processing…',
      successMsg: 'Your order has been placed!',
      successSub: "We'll be in touch soon.",
      close: 'Close',
      viewOrders: 'View Orders',
    },
    shipping: {
      firstName: 'First Name',
      lastName: 'Last Name',
      email: 'Email',
      phone: 'Phone',
      address: 'Address',
      addressPlaceholder: 'Street address',
      addressLine2Placeholder: 'Apartment, suite, etc. (optional)',
      city: 'City',
      postCode: 'Post Code',
      country: 'Country',
      saveDetails: 'Save details for next time',
    },
    lightbox: {
      orderPrint: 'Order Print',
    },
    footer: {
      support: 'Support',
      privacy: 'Privacy Policy',
      terms: 'Terms & Conditions',
      scta: '特定商取引法に基づく表記',
      brand: 'A product of Nakama AI',
    },
    confirm: {
      regenerate: 'Regenerate this portrait? The current result will be replaced.',
    },
    backToHome: '← Back to Home',
    auth: {
      signIn: 'Sign In',
      signUp: 'Create Account',
      email: 'Email',
      password: 'Password',
      forgotPassword: 'Forgot password?',
      sendResetEmail: 'Send reset email',
      confirmPassword: 'Confirm Password',
      passwordMismatch: 'Passwords do not match.',
      resetSent: 'Password reset email sent — check your inbox.',
      orContinueWith: 'or continue with',
      noAccount: "Don't have an account? Sign up",
      hasAccount: 'Already have an account? Sign in',
      submitting: 'Please wait…',
    },
  },

  ja: {
    nav: {
      home: 'ホーム',
      createPortrait: 'ポートレート作成',
      orders: '注文',
      myGenerations: 'マイ作品',
      signIn: 'ログイン',
      signOut: 'ログアウト',
    },
    hero: {
      line1: 'ペットを',
      accent: '江戸絵画に変える',
      subtitle: '写真をアップロードして、浮世絵の巨匠にインスパイアされたスタイルをお選びください。',
      cta: 'ポートレートを作成',
    },
    create: {
      step1: '1 · ペット写真をアップロード',
      step2: '2 · スタイルを選択',
      step3: '3 · 向き',
      dryRun: 'ドライラン',
      dryRunHint: '（プロンプトを出力・RunPodをスキップ）',
      generate: 'ポートレートを生成',
      generateDry: '生成（ドライラン）',
      submitting: '送信中…',
      orderPrint: 'プリントを注文',
      generating: '生成中',
    },
    gallery: {
      community: 'コミュニティ',
      loading: '読み込み中…',
      noSamples: 'サンプルはまだありません',
      noSamplesHint: '江戸風ポートレートのサンプルをお楽しみに',
    },
    styles: {
      seeAll: 'すべて見る',
      exploreStyles: 'スタイルを探す',
      selectStyle: 'スタイルを選択',
    },
    bottomBar: {
      home: 'ホーム',
      create: '作成',
      orders: '注文',
      gallery: 'ギャラリー',
    },
    queue: {
      view: '表示',
      tryAgain: '↺ 再生成',
      failed: '生成に失敗しました',
      status: {
        pending: '待機中',
        processing: '生成中',
        fixing: '修正中',
        completed: '完了',
        failed: '失敗',
      },
    },
    past: {
      title: 'プリントを注文する',
      refresh: '更新',
      empty: 'まだポートレートがありません — 上で生成してください！',
      deselect: '選択解除',
      selectForOrder: '注文に追加',
      delete: '削除',
    },
    upload: {
      drop: 'ペットの写真をここにドロップ',
      hint: 'PNG · JPG · WEBP  ·  またはクリックして参照',
      changePhoto: '写真を変更',
    },
    orders: {
      title: '注文一覧',
      refresh: '更新',
      empty: 'まだ注文がありません。',
      emptyHint: 'ギャラリーから作品を選択して「ポートレートを注文」をタップしてください。',
      paid: '支払済',
      unpaid: '未払い',
      edit: '編集',
      payNow: '今すぐ支払う',
      processing: '処理中…',
      paidOn: 'お支払い日',
      deliveryMsg: 'ご注文を承りました。お支払い確認後、10〜14営業日以内にお届けいたします。',
      emailSentTo: '確認メールを送信しました：',
    },
    orderFlow: {
      configurePrints: 'プリントを設定',
      shipping: '配送先',
      done: '完了',
      selectFrame: 'フレームを選択',
      color: 'カラー',
      size: 'サイズ',
      orientation: '向き',
      portrait: '縦向き',
      landscape: '横向き',
      qty: '数量',
      total: '合計',
      cancel: 'キャンセル',
      shippingDetails: '配送先の詳細',
      saving: '保存中…',
      back: '← 戻る',
      payNow: '今すぐ支払う',
      processing: '処理中…',
      successMsg: 'ご注文が完了しました！',
      successSub: 'まもなくご連絡いたします。',
      close: '閉じる',
      viewOrders: '注文を確認',
    },
    shipping: {
      firstName: '名',
      lastName: '姓',
      email: 'メールアドレス',
      phone: '電話番号',
      address: '住所',
      addressPlaceholder: '番地・建物名',
      addressLine2Placeholder: '部屋番号など（任意）',
      city: '市区町村',
      postCode: '郵便番号',
      country: '国',
      saveDetails: '次回のために保存',
    },
    lightbox: {
      orderPrint: 'プリントを注文',
    },
    footer: {
      support: 'サポート',
      privacy: 'プライバシーポリシー',
      terms: '利用規約',
      scta: '特定商取引法に基づく表記',
      brand: 'Nakama AI のプロダクト',
    },
    confirm: {
      regenerate: 'このポートレートを再生成しますか？現在の結果は置き換えられます。',
    },
    backToHome: '← ホームへ戻る',
    auth: {
      signIn: 'ログイン',
      signUp: 'アカウント作成',
      email: 'メールアドレス',
      password: 'パスワード',
      forgotPassword: 'パスワードをお忘れですか？',
      sendResetEmail: 'リセットメールを送信',
      confirmPassword: 'パスワード（確認）',
      passwordMismatch: 'パスワードが一致しません。',
      resetSent: 'パスワードリセットメールを送信しました。受信トレイをご確認ください。',
      orContinueWith: 'または',
      noAccount: 'アカウントをお持ちでない方はこちら',
      hasAccount: 'すでにアカウントをお持ちの方はこちら',
      submitting: 'しばらくお待ちください…',
    },
  },
};
