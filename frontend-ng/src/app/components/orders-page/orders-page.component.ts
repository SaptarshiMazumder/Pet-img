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
    this.api.createPayment(order.id).subscribe({
      next: (data) => {
        const options = {
          key: data.key_id,
          amount: data.amount,
          currency: data.currency,
          name: 'Pet Generator',
          description: 'ポートレート印刷注文',
          order_id: data.razorpay_order_id,
          language: 'ja',
          prefill: {
            name: `${order.shipping.firstName} ${order.shipping.lastName}`,
            email: order.shipping.email,
            contact: order.shipping.phone || '',
          },
          handler: (response: any) => {
            this.api.verifyPayment(order.id, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            }).subscribe({
              next: () => { this.payingId = null; this.refresh.emit(); },
              error: () => { this.payingId = null; this.payError = 'Payment verification failed.'; },
            });
          },
          modal: { hide_topbar: true, ondismiss: () => { this.payingId = null; } },
        };
        new (window as any).Razorpay(options).open();
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
