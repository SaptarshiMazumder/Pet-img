import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GalleryEntry, Order, ShippingAddress } from '../../models';
import { ApiService } from '../../services/api.service';
import { LanguageService } from '../../services/language.service';

export interface FrameVariant {
  color: string;
  preview_img_landscape: string;
  preview_img_portrait: string;
}

export interface FrameCategory {
  name: string;
  overlay_inset: number;
  variants: FrameVariant[];
  sizes: { [key: string]: { price: number } };
}

export interface ItemConfig {
  item: GalleryEntry;
  category: string;
  color: string;
  size: string;
  orientation: 'portrait' | 'landscape';
  lockedOrientation?: 'portrait' | 'landscape';
  quantity: number;
}

const SHIPPING_KEY = 'pg_shipping';

/** Countries that have print fulfilment set up */
const SUPPORTED_REGION_MAP: Record<string, 'JP' | 'IN'> = {
  JP: 'JP',
  IN: 'IN',
};

export const COUNTRY_LIST: { code: string; en: string; ja: string }[] = [
  { code: 'AF', en: 'Afghanistan', ja: 'アフガニスタン' },
  { code: 'AL', en: 'Albania', ja: 'アルバニア' },
  { code: 'DZ', en: 'Algeria', ja: 'アルジェリア' },
  { code: 'AR', en: 'Argentina', ja: 'アルゼンチン' },
  { code: 'AM', en: 'Armenia', ja: 'アルメニア' },
  { code: 'AU', en: 'Australia', ja: 'オーストラリア' },
  { code: 'AT', en: 'Austria', ja: 'オーストリア' },
  { code: 'AZ', en: 'Azerbaijan', ja: 'アゼルバイジャン' },
  { code: 'BD', en: 'Bangladesh', ja: 'バングラデシュ' },
  { code: 'BE', en: 'Belgium', ja: 'ベルギー' },
  { code: 'BO', en: 'Bolivia', ja: 'ボリビア' },
  { code: 'BA', en: 'Bosnia and Herzegovina', ja: 'ボスニア・ヘルツェゴビナ' },
  { code: 'BR', en: 'Brazil', ja: 'ブラジル' },
  { code: 'BG', en: 'Bulgaria', ja: 'ブルガリア' },
  { code: 'KH', en: 'Cambodia', ja: 'カンボジア' },
  { code: 'CA', en: 'Canada', ja: 'カナダ' },
  { code: 'CL', en: 'Chile', ja: 'チリ' },
  { code: 'CN', en: 'China', ja: '中国' },
  { code: 'CO', en: 'Colombia', ja: 'コロンビア' },
  { code: 'HR', en: 'Croatia', ja: 'クロアチア' },
  { code: 'CZ', en: 'Czech Republic', ja: 'チェコ共和国' },
  { code: 'DK', en: 'Denmark', ja: 'デンマーク' },
  { code: 'EC', en: 'Ecuador', ja: 'エクアドル' },
  { code: 'EG', en: 'Egypt', ja: 'エジプト' },
  { code: 'EE', en: 'Estonia', ja: 'エストニア' },
  { code: 'ET', en: 'Ethiopia', ja: 'エチオピア' },
  { code: 'FI', en: 'Finland', ja: 'フィンランド' },
  { code: 'FR', en: 'France', ja: 'フランス' },
  { code: 'GE', en: 'Georgia', ja: 'ジョージア' },
  { code: 'DE', en: 'Germany', ja: 'ドイツ' },
  { code: 'GH', en: 'Ghana', ja: 'ガーナ' },
  { code: 'GR', en: 'Greece', ja: 'ギリシャ' },
  { code: 'HK', en: 'Hong Kong', ja: '香港' },
  { code: 'HU', en: 'Hungary', ja: 'ハンガリー' },
  { code: 'IS', en: 'Iceland', ja: 'アイスランド' },
  { code: 'IN', en: 'India', ja: 'インド' },
  { code: 'ID', en: 'Indonesia', ja: 'インドネシア' },
  { code: 'IE', en: 'Ireland', ja: 'アイルランド' },
  { code: 'IL', en: 'Israel', ja: 'イスラエル' },
  { code: 'IT', en: 'Italy', ja: 'イタリア' },
  { code: 'JP', en: 'Japan', ja: '日本' },
  { code: 'JO', en: 'Jordan', ja: 'ヨルダン' },
  { code: 'KZ', en: 'Kazakhstan', ja: 'カザフスタン' },
  { code: 'KE', en: 'Kenya', ja: 'ケニア' },
  { code: 'KR', en: 'South Korea', ja: '韓国' },
  { code: 'KW', en: 'Kuwait', ja: 'クウェート' },
  { code: 'KG', en: 'Kyrgyzstan', ja: 'キルギス' },
  { code: 'LA', en: 'Laos', ja: 'ラオス' },
  { code: 'LV', en: 'Latvia', ja: 'ラトビア' },
  { code: 'LB', en: 'Lebanon', ja: 'レバノン' },
  { code: 'LT', en: 'Lithuania', ja: 'リトアニア' },
  { code: 'LU', en: 'Luxembourg', ja: 'ルクセンブルク' },
  { code: 'MY', en: 'Malaysia', ja: 'マレーシア' },
  { code: 'MX', en: 'Mexico', ja: 'メキシコ' },
  { code: 'MD', en: 'Moldova', ja: 'モルドバ' },
  { code: 'MN', en: 'Mongolia', ja: 'モンゴル' },
  { code: 'MA', en: 'Morocco', ja: 'モロッコ' },
  { code: 'MM', en: 'Myanmar', ja: 'ミャンマー' },
  { code: 'NP', en: 'Nepal', ja: 'ネパール' },
  { code: 'NL', en: 'Netherlands', ja: 'オランダ' },
  { code: 'NZ', en: 'New Zealand', ja: 'ニュージーランド' },
  { code: 'NG', en: 'Nigeria', ja: 'ナイジェリア' },
  { code: 'NO', en: 'Norway', ja: 'ノルウェー' },
  { code: 'OM', en: 'Oman', ja: 'オマーン' },
  { code: 'PK', en: 'Pakistan', ja: 'パキスタン' },
  { code: 'PY', en: 'Paraguay', ja: 'パラグアイ' },
  { code: 'PE', en: 'Peru', ja: 'ペルー' },
  { code: 'PH', en: 'Philippines', ja: 'フィリピン' },
  { code: 'PL', en: 'Poland', ja: 'ポーランド' },
  { code: 'PT', en: 'Portugal', ja: 'ポルトガル' },
  { code: 'QA', en: 'Qatar', ja: 'カタール' },
  { code: 'RO', en: 'Romania', ja: 'ルーマニア' },
  { code: 'RU', en: 'Russia', ja: 'ロシア' },
  { code: 'SA', en: 'Saudi Arabia', ja: 'サウジアラビア' },
  { code: 'SN', en: 'Senegal', ja: 'セネガル' },
  { code: 'RS', en: 'Serbia', ja: 'セルビア' },
  { code: 'SG', en: 'Singapore', ja: 'シンガポール' },
  { code: 'SK', en: 'Slovakia', ja: 'スロバキア' },
  { code: 'SI', en: 'Slovenia', ja: 'スロベニア' },
  { code: 'ZA', en: 'South Africa', ja: '南アフリカ' },
  { code: 'ES', en: 'Spain', ja: 'スペイン' },
  { code: 'LK', en: 'Sri Lanka', ja: 'スリランカ' },
  { code: 'SE', en: 'Sweden', ja: 'スウェーデン' },
  { code: 'CH', en: 'Switzerland', ja: 'スイス' },
  { code: 'TW', en: 'Taiwan', ja: '台湾' },
  { code: 'TZ', en: 'Tanzania', ja: 'タンザニア' },
  { code: 'TH', en: 'Thailand', ja: 'タイ' },
  { code: 'TR', en: 'Turkey', ja: 'トルコ' },
  { code: 'UG', en: 'Uganda', ja: 'ウガンダ' },
  { code: 'UA', en: 'Ukraine', ja: 'ウクライナ' },
  { code: 'AE', en: 'United Arab Emirates', ja: 'アラブ首長国連邦' },
  { code: 'GB', en: 'United Kingdom', ja: 'イギリス' },
  { code: 'US', en: 'United States', ja: 'アメリカ合衆国' },
  { code: 'UY', en: 'Uruguay', ja: 'ウルグアイ' },
  { code: 'UZ', en: 'Uzbekistan', ja: 'ウズベキスタン' },
  { code: 'VE', en: 'Venezuela', ja: 'ベネズエラ' },
  { code: 'VN', en: 'Vietnam', ja: 'ベトナム' },
  { code: 'ZM', en: 'Zambia', ja: 'ザンビア' },
  { code: 'ZW', en: 'Zimbabwe', ja: 'ジンバブエ' },
];

@Component({
  selector: 'app-order-flow',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './order-flow.component.html',
  styleUrl: './order-flow.component.css',
})
export class OrderFlowComponent implements OnChanges, OnInit {
  protected readonly lang = inject(LanguageService);
  @Input() items: GalleryEntry[] = [];
  @Input() editOrder: Order | null = null;
  @Output() closed = new EventEmitter<void>();
  @Output() orderPlaced = new EventEmitter<void>();
  @Output() viewOrders = new EventEmitter<void>();

  step: 1 | 2 | 'success' = 1;
  submitting = false;
  savingDraft = false;
  error = '';
  existingOrderId: string | null = null;

  readonly countryList = COUNTRY_LIST;
  selectedCountry = 'IN';
  region: 'JP' | 'IN' = 'IN';
  categories: FrameCategory[] = [];
  itemConfigs: ItemConfig[] = [];

  get shippingAvailable(): boolean {
    return !!SUPPORTED_REGION_MAP[this.selectedCountry];
  }
  shipping: ShippingAddress = this.defaultShipping();
  saveShipping = true;

  get currencySymbol(): string { return this.region === 'IN' ? '₹' : '¥'; }

  constructor(public api: ApiService) {}

  ngOnInit() {
    this.loadCatalog();
  }

  private loadCatalog() {
    this.api.getFrameCatalog(this.region).subscribe({
      next: (data) => {
        this.categories = data.categories;
        if (this.itemConfigs.length && this.categories.length) {
          this.itemConfigs.forEach(c => this.applyDefaults(c));
        }
      },
      error: () => {},
    });
  }

  onCountryChange() {
    const r = SUPPORTED_REGION_MAP[this.selectedCountry];
    if (r && r !== this.region) {
      this.region = r;
      this.categories = [];
      this.shipping.country = this.selectedCountry;
      this.loadCatalog();
    } else if (!r) {
      this.categories = [];
    }
    this.shipping.country = this.selectedCountry;
  }

  onRegionChange() {
    this.categories = [];
    this.shipping.country = this.region === 'IN' ? 'IN' : 'JP';
    this.loadCatalog();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['items']?.currentValue?.length || changes['editOrder']) {
      this.reset();
    }
  }

  private reset() {
    this.step = 1;
    this.error = '';
    this.submitting = false;
    this.savingDraft = false;
    this.existingOrderId = this.editOrder?.id ?? null;

    if (this.editOrder) {
      this.itemConfigs = this.items
        .filter(i => i.presigned_url)
        .map((item, idx) => {
          const oi = this.editOrder!.items[idx];
          const locked = (item.orientation ?? oi?.orientation) as 'portrait' | 'landscape' | undefined;
          const cfg: ItemConfig = {
            item,
            category: oi?.category ?? '',
            color: oi?.color ?? '',
            size: oi?.size ?? '',
            orientation: locked ?? (oi?.orientation as any) ?? 'portrait',
            lockedOrientation: locked,
            quantity: oi?.quantity ?? 1,
          };
          this.applyDefaults(cfg);
          return cfg;
        });
      this.shipping = { ...this.defaultShipping(), ...this.editOrder.shipping };
    } else {
      this.itemConfigs = this.items
        .filter(i => i.presigned_url)
        .map(item => {
          const locked = item.orientation;
          const cfg: ItemConfig = { item, category: '', color: '', size: '', orientation: locked ?? 'portrait', lockedOrientation: locked, quantity: 1 };
          this.applyDefaults(cfg);
          return cfg;
        });
      this.shipping = this.loadShipping();
    }
  }

  private applyDefaults(cfg: ItemConfig) {
    const firstCat = this.categories[0];
    if (!firstCat) return;
    const cat = this.categories.find(c => c.name === cfg.category) ?? firstCat;
    cfg.category = cat.name;
    if (!cat.variants.find(v => v.color === cfg.color)) cfg.color = cat.variants[0]?.color ?? '';
    const sizeKeys = Object.keys(cat.sizes);
    if (!sizeKeys.includes(cfg.size)) cfg.size = sizeKeys[0] ?? '';
    if (cfg.item.orientation) cfg.orientation = cfg.item.orientation;
  }

  categoryFor(cfg: ItemConfig): FrameCategory | undefined {
    return this.categories.find(c => c.name === cfg.category);
  }

  selectCategory(cfg: ItemConfig, catName: string) {
    cfg.category = catName;
    const cat = this.categories.find(c => c.name === catName);
    if (cat) {
      cfg.color = cat.variants[0]?.color ?? '';
      const keys = Object.keys(cat.sizes);
      if (!keys.includes(cfg.size)) cfg.size = keys[0] ?? '';
    }
  }

  onColorChange(_cfg: ItemConfig) {}

  onOrientationChange(cfg: ItemConfig, orientation: 'portrait' | 'landscape') {
    cfg.orientation = orientation;
  }

  frameCoverImg(cfg: ItemConfig, cat: FrameCategory): string {
    const variant = cfg.category === cat.name
      ? (cat.variants.find(v => v.color === cfg.color) ?? cat.variants[0])
      : cat.variants[0];
    if (!variant) return '';
    const img = cfg.orientation === 'landscape' ? variant.preview_img_landscape : variant.preview_img_portrait;
    return img ? this.api.assetUrl(img) : '';
  }

  selectedFrameImg(cfg: ItemConfig): string {
    const cat = this.categoryFor(cfg);
    if (!cat) return '';
    const variant = cat.variants.find(v => v.color === cfg.color) ?? cat.variants[0];
    if (!variant) return '';
    const img = cfg.orientation === 'landscape' ? variant.preview_img_landscape : variant.preview_img_portrait;
    return img ? this.api.assetUrl(img) : '';
  }

  frameOverlayStyle(cfg: ItemConfig): { [key: string]: string } {
    const inset = this.categoryFor(cfg)?.overlay_inset ?? 10;
    return {
      top: `-${inset}%`,
      left: `-${inset}%`,
      width: `${100 + inset * 2}%`,
      height: `${100 + inset * 2}%`,
    };
  }

  frameCompositeStyle(cfg: ItemConfig): { [key: string]: string } {
    const inset = this.categoryFor(cfg)?.overlay_inset ?? 10;
    const pct = (100 / (1 + (2 * inset) / 100)).toFixed(2);
    return {
      'max-width': `${pct}%`,
      'margin': `${inset}% auto`,
    };
  }

  sizeKeys(cfg: ItemConfig): string[] {
    return Object.keys(this.categoryFor(cfg)?.sizes ?? {});
  }

  currentPrice(cfg: ItemConfig): number {
    const cat = this.categoryFor(cfg);
    return (cat?.sizes[cfg.size]?.price ?? 0) * cfg.quantity;
  }

  private defaultShipping(): ShippingAddress {
    return { firstName: '', lastName: '', email: '', phone: '', addressLine1: '', addressLine2: '', city: '', postCode: '', country: this.selectedCountry };
  }

  private loadShipping(): ShippingAddress {
    try {
      const saved = localStorage.getItem(SHIPPING_KEY);
      return saved ? { ...this.defaultShipping(), ...JSON.parse(saved) } : this.defaultShipping();
    } catch { return this.defaultShipping(); }
  }

  goToShipping() {
    this.error = '';
    this.savingDraft = true;
    const cfg = this.itemConfigs[0];
    const payload = {
      region: this.region,
      items: [{
        job_id: cfg.item.job_id,
        presigned_url: cfg.item.presigned_url,
        template_key: cfg.item.template_key,
        category: cfg.category,
        size: cfg.size,
        color: cfg.color,
        orientation: cfg.orientation,
        quantity: cfg.quantity,
      }],
      shipping: this.shipping,
      status: 'draft',
    };
    if (this.existingOrderId) {
      this.api.updateOrder(this.existingOrderId, payload).subscribe({
        next: () => { this.savingDraft = false; this.step = 2; },
        error: () => { this.savingDraft = false; this.step = 2; },
      });
    } else {
      this.api.createOrder(payload).subscribe({
        next: (resp: any) => { this.existingOrderId = resp.order_id; this.savingDraft = false; this.step = 2; },
        error: () => { this.savingDraft = false; this.step = 2; },
      });
    }
  }

  submit() {
    const s = this.shipping;
    if (!s.firstName || !s.lastName || !s.email || !s.addressLine1 || !s.city || !s.postCode) {
      this.error = 'Please fill in all required fields.';
      return;
    }
    if (this.saveShipping) {
      try { localStorage.setItem(SHIPPING_KEY, JSON.stringify(this.shipping)); } catch {}
    }
    this.submitting = true;
    this.error = '';
    const cfg = this.itemConfigs[0];
    const payload = {
      region: this.region,
      items: [{
        job_id: cfg.item.job_id,
        presigned_url: cfg.item.presigned_url,
        template_key: cfg.item.template_key,
        category: cfg.category,
        size: cfg.size,
        color: cfg.color,
        orientation: cfg.orientation,
        quantity: cfg.quantity,
      }],
      shipping: this.shipping,
    };
    if (this.existingOrderId) {
      this.api.updateOrder(this.existingOrderId, payload).subscribe({
        next: () => { this.submitting = false; this.step = 'success'; this.orderPlaced.emit(); },
        error: (err: any) => { this.submitting = false; this.error = err?.error?.error || 'Failed to update order.'; },
      });
    } else {
      this.api.createOrder(payload).subscribe({
        next: (resp: any) => { this.existingOrderId = resp.order_id; this.submitting = false; this.step = 'success'; this.orderPlaced.emit(); },
        error: (err: any) => { this.submitting = false; this.error = err?.error?.error || 'Failed to create order.'; },
      });
    }
  }
}
