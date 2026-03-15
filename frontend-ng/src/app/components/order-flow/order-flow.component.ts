import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { forkJoin } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { GalleryEntry, ShippingAddress } from '../../models';
import { ApiService } from '../../services/api.service';

export interface ItemConfig {
  item: GalleryEntry;
  size: string;
  print_type: string;
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
export class OrderFlowComponent implements OnChanges {
  @Input() items: GalleryEntry[] = [];
  @Output() closed = new EventEmitter<void>();
  @Output() orderPlaced = new EventEmitter<void>();
  @Output() viewOrders = new EventEmitter<void>();

  step: 1 | 2 | 'success' = 1;
  submitting = false;
  error = '';
  orderId = '';

  readonly printTypes = ['Glossy', 'Matte', 'Canvas', 'Framed'];
  readonly sizeOptions = ['A4', 'A3', 'A2', 'Square 30×30 cm'];

  itemConfigs: ItemConfig[] = [];
  shipping: ShippingAddress = this.defaultShipping();
  saveShipping = true;

  constructor(private api: ApiService) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['items']?.currentValue?.length) {
      this.reset();
    }
  }

  private reset() {
    this.step = 1;
    this.error = '';
    this.submitting = false;
    this.orderId = '';
    this.itemConfigs = this.items
      .filter(i => i.presigned_url)
      .map(item => ({ item, size: 'A4', print_type: 'Glossy', quantity: 1 }));
    this.shipping = this.loadShipping();
  }

  private defaultShipping(): ShippingAddress {
    return {
      firstName: '', lastName: '', email: '', phone: '',
      addressLine1: '', addressLine2: '', city: '', postCode: '', country: 'JP',
    };
  }

  private loadShipping(): ShippingAddress {
    try {
      const saved = localStorage.getItem(SHIPPING_KEY);
      return saved ? { ...this.defaultShipping(), ...JSON.parse(saved) } : this.defaultShipping();
    } catch {
      return this.defaultShipping();
    }
  }

  goToShipping() {
    this.error = '';
    this.step = 2;
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

    const requests = this.itemConfigs.map(cfg =>
      this.api.createOrder({
        items: [{
          job_id: cfg.item.job_id,
          presigned_url: cfg.item.presigned_url,
          template_key: cfg.item.template_key,
          size: cfg.size,
          print_type: cfg.print_type,
          quantity: cfg.quantity,
        }],
        shipping: this.shipping,
      })
    );

    forkJoin(requests).subscribe({
      next: () => {
        this.submitting = false;
        this.step = 'success';
        this.orderPlaced.emit();
      },
      error: (err: any) => {
        this.submitting = false;
        this.error = err?.error?.error || 'Failed to place order. Please try again.';
      },
    });
  }
}
