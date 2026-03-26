import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { Order } from '../../models';
import { AuthService } from '../../services/auth.service';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [],
  templateUrl: './orders-page.component.html',
  styleUrl: './orders-page.component.css',
})
export class OrdersPageComponent {
  protected readonly lang = inject(LanguageService);
  protected readonly auth = inject(AuthService);
  @Input() orders: Order[] = [];
  @Input() loading = false;
  @Output() refresh = new EventEmitter<void>();
  @Output() editOrder = new EventEmitter<Order>();


  formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  itemSummary(item: any): string {
    const parts = [item.template_key, item.category, item.size, item.color, `×${item.quantity}`];
    return parts.filter(Boolean).join(' · ');
  }
}
