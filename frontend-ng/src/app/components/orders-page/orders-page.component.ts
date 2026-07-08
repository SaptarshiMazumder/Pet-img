import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { Order } from '../../models';
import { ApiService } from '../../services/api.service';
import { LanguageService } from '../../services/language.service';
import { LocationService } from '../../services/location.service';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [],
  templateUrl: './orders-page.component.html',
  styleUrl: './orders-page.component.css',
})
export class OrdersPageComponent {
  protected readonly lang = inject(LanguageService);
  protected readonly location = inject(LocationService);
  readonly orderingEnabled = false;
  @Input() orders: Order[] = [];
  @Input() loading = false;
  @Output() refresh = new EventEmitter<void>();
  @Output() editOrder = new EventEmitter<Order>();

  submittingId: string | null = null;
  submitError = '';

  constructor(private api: ApiService) {}

  submit(order: Order) {
    if (this.hasUnsupportedShippingCountry(order.shipping.country)) {
      this.submitError = this.lang.t().region.noShippingBanner;
      return;
    }

    if (!this.orderingEnabled) {
      return;
    }

    this.submittingId = order.id;
    this.submitError = '';
    this.api.submitOrder(order.id, this.lang.lang()).subscribe({
      next: () => {
        this.submittingId = null;
        this.refresh.emit();
      },
      error: (err: any) => {
        this.submittingId = null;
        this.submitError = err?.error?.error || 'Failed to submit order.';
      },
    });
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  itemSummary(item: any): string {
    const parts = [item.template_key, item.category, item.size, item.color, `×${item.quantity}`];
    return parts.filter(Boolean).join(' · ');
  }
  hasUnsupportedShippingCountry(country: string): boolean {
    return this.location.hasUnsupportedShippingCountry(country);
  }
}
