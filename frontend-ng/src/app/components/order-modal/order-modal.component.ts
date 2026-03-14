import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { JobEntry, OrderForm } from '../../models';

@Component({
  selector: 'app-order-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './order-modal.component.html',
  styleUrl: './order-modal.component.css',
})
export class OrderModalComponent implements OnChanges {
  @Input() job: JobEntry | null = null;
  @Input() products: { uid: string; label: string }[] = [];
  @Input() productsLoading = false;
  @Input() submitting = false;
  @Input() error = '';
  @Input() success = '';
  @Output() closed = new EventEmitter<void>();
  @Output() submitted = new EventEmitter<OrderForm>();

  form: OrderForm = this.defaultForm();

  ngOnChanges(changes: SimpleChanges) {
    if (changes['job'] && changes['job'].currentValue && !changes['job'].previousValue) {
      this.form = this.defaultForm();
    }
    if (changes['products']) {
      const prods: { uid: string; label: string }[] = changes['products'].currentValue ?? [];
      if (prods.length > 0 && !this.form.product_uid) {
        this.form.product_uid = prods[0].uid;
      }
    }
  }

  private defaultForm(): OrderForm {
    return {
      firstName: '',
      lastName: '',
      addressLine1: '',
      addressLine2: '',
      city: '',
      postCode: '',
      country: 'JP',
      email: '',
      phone: '',
      product_uid: '',
      quantity: 1,
      order_type: 'draft',
    };
  }
}
