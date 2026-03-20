import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Order } from '../../models';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [],
  templateUrl: './orders-page.component.html',
  styleUrl: './orders-page.component.css',
})
export class OrdersPageComponent {
  @Input() orders: Order[] = [];
  @Input() loading = false;
  @Output() refresh = new EventEmitter<void>();
  @Output() editOrder = new EventEmitter<Order>();

  payingId: string | null = null;
  payError = '';

  constructor(private api: ApiService) {}

  pay(order: Order) {
    this.payingId = order.id;
    this.payError = '';
    const returnUrl = `${window.location.origin}/?payment_return=1`;
    this.api.createPayment(order.id, returnUrl).subscribe({
      next: (data) => {
        window.open(data.session_url, 'komoju-payment', 'width=620,height=720,scrollbars=yes');
        const handler = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          if (event.data?.type === 'komoju_return') {
            window.removeEventListener('message', handler);
            this.api.verifyPayment(order.id).subscribe({
              next: () => { this.payingId = null; this.refresh.emit(); },
              error: () => { this.payingId = null; this.payError = 'Payment verification failed.'; },
            });
          }
        };
        window.addEventListener('message', handler);
      },
      error: (err: any) => {
        this.payingId = null;
        this.payError = err?.error?.error || 'Failed to initiate payment.';
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
}
