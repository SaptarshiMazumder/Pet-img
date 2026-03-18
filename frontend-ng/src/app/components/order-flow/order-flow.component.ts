import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GalleryEntry, Order, ShippingAddress } from '../../models';
import { ApiService } from '../../services/api.service';

export interface FrameVariant {
  color: string;
  preview_img: string;
}

export interface FrameCategory {
  name: string;
  variants: FrameVariant[];
  sizes: { [key: string]: { price: number } };
}

export interface ItemConfig {
  item: GalleryEntry;
  category: string;
  color: string;
  size: string;
  orientation: 'portrait' | 'landscape';
  quantity: number;
}

const SHIPPING_KEY = 'pg_shipping';

@Component({
  selector: 'app-order-flow',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './order-flow.component.html',
  styleUrl: './order-flow.component.css',
})
export class OrderFlowComponent implements OnChanges, OnInit {
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

  categories: FrameCategory[] = [];
  itemConfigs: ItemConfig[] = [];
  shipping: ShippingAddress = this.defaultShipping();
  saveShipping = true;

  constructor(public api: ApiService) {}

  ngOnInit() {
    this.api.getFrameCatalog().subscribe({
      next: (data) => {
        this.categories = data.categories;
        if (this.itemConfigs.length && this.categories.length) {
          this.itemConfigs.forEach(c => this.applyDefaults(c));
        }
      },
      error: () => {},
    });
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
      // Pre-populate from existing order
      this.itemConfigs = this.items
        .filter(i => i.presigned_url)
        .map((item, idx) => {
          const oi = this.editOrder!.items[idx];
          const cfg: ItemConfig = {
            item,
            category: oi?.category ?? '',
            color: oi?.color ?? '',
            size: oi?.size ?? '',
            orientation: (oi?.orientation as any) ?? 'portrait',
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
          const cfg: ItemConfig = { item, category: '', color: '', size: '', orientation: 'portrait', quantity: 1 };
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

  frameCoverImg(cfg: ItemConfig, cat: FrameCategory): string {
    const variant = cfg.category === cat.name
      ? (cat.variants.find(v => v.color === cfg.color) ?? cat.variants[0])
      : cat.variants[0];
    return variant ? this.api.assetUrl(variant.preview_img) : '';
  }

  sizeKeys(cfg: ItemConfig): string[] {
    return Object.keys(this.categoryFor(cfg)?.sizes ?? {});
  }

  currentPrice(cfg: ItemConfig): number {
    const cat = this.categoryFor(cfg);
    return (cat?.sizes[cfg.size]?.price ?? 0) * cfg.quantity;
  }

  private defaultShipping(): ShippingAddress {
    return { firstName: '', lastName: '', email: '', phone: '', addressLine1: '', addressLine2: '', city: '', postCode: '', country: 'JP' };
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
        next: () => { this.openPayment(this.existingOrderId!); },
        error: (err: any) => { this.submitting = false; this.error = err?.error?.error || 'Failed to update order.'; },
      });
    } else {
      this.api.createOrder(payload).subscribe({
        next: (resp: any) => { this.existingOrderId = resp.order_id; this.openPayment(resp.order_id); },
        error: (err: any) => { this.submitting = false; this.error = err?.error?.error || 'Failed to create order.'; },
      });
    }
  }

  private openPayment(orderId: string) {
    this.api.createPayment(orderId).subscribe({
      next: (data) => {
        this.submitting = false;
        const options = {
          key: data.key_id,
          amount: data.amount,
          currency: data.currency,
          name: 'Pet Generator',
          description: 'ポートレート印刷注文',
          order_id: data.razorpay_order_id,
          language: 'ja',
          prefill: {
            name: `${this.shipping.firstName} ${this.shipping.lastName}`,
            email: this.shipping.email,
            contact: this.shipping.phone || '',
          },
          handler: (response: any) => {
            this.api.verifyPayment(orderId, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            }).subscribe({
              next: () => { this.step = 'success'; this.orderPlaced.emit(); },
              error: () => { this.error = 'Payment verification failed. Contact support.'; },
            });
          },
          modal: { hide_topbar: true, ondismiss: () => {} },
        };
        new (window as any).Razorpay(options).open();
      },
      error: (err: any) => { this.submitting = false; this.error = err?.error?.error || 'Failed to initiate payment.'; },
    });
  }
}
