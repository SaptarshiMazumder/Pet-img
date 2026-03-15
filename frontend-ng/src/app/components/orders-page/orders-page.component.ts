import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Order, OrderItem, ShippingAddress } from '../../models';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './orders-page.component.html',
  styleUrl: './orders-page.component.css',
})
export class OrdersPageComponent implements OnChanges {
  @Input() orders: Order[] = [];
  @Input() loading = false;
  @Output() refresh = new EventEmitter<void>();

  editingId: string | null = null;
  editShipping: ShippingAddress | null = null;
  editItems: OrderItem[] | null = null;
  savingId: string | null = null;
  saveError = '';

  readonly printTypes = ['Glossy', 'Matte', 'Canvas', 'Framed'];
  readonly sizeOptions = ['A4', 'A3', 'A2', 'Square 30×30 cm'];

  constructor(private api: ApiService) {}

  ngOnChanges(changes: SimpleChanges) {
    // clear any stale edit state when orders reload
    if (changes['orders']) {
      this.editingId = null;
      this.editShipping = null;
    }
  }

  startEdit(order: Order) {
    this.editingId = order.id;
    this.editShipping = { ...order.shipping };
    this.editItems = order.items.map(i => ({ ...i }));
    this.saveError = '';
  }

  cancelEdit() {
    this.editingId = null;
    this.editShipping = null;
    this.editItems = null;
    this.saveError = '';
  }

  saveEdit(order: Order) {
    if (!this.editShipping || !this.editItems) return;
    this.savingId = order.id;
    this.saveError = '';

    this.api.updateOrder(order.id, { shipping: this.editShipping, items: this.editItems }).subscribe({
      next: () => {
        this.savingId = null;
        this.editingId = null;
        this.editShipping = null;
        this.editItems = null;
        this.refresh.emit();
      },
      error: (err: any) => {
        this.savingId = null;
        this.saveError = err?.error?.error || 'Failed to save changes.';
      },
    });
  }

  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  itemSummary(order: Order): string {
    return order.items
      .map(i => `${i.template_key} · ${i.print_type} ${i.size} ×${i.quantity}`)
      .join('\n');
  }
}
