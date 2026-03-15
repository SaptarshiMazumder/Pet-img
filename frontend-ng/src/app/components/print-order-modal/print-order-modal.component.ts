import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GalleryEntry } from '../../models';

interface PrintOrderForm {
  firstName: string; lastName: string; email: string; phone: string;
  addressLine1: string; addressLine2: string; city: string; postCode: string;
  country: string; size: string; quantity: number; notes: string;
}
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-print-order-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './print-order-modal.component.html',
  styleUrl: './print-order-modal.component.css',
})
export class PrintOrderModalComponent implements OnChanges {
  @Input() items: GalleryEntry[] = [];
  @Output() closed = new EventEmitter<void>();
  @Output() orderPlaced = new EventEmitter<string>(); // emits the new order_id

  submitting = false;
  error = '';
  success = '';

  readonly sizeOptions = ['A4', 'A3', 'A2', 'Square (20×20 cm)'];

  form: PrintOrderForm = this.defaultForm();

  constructor(private api: ApiService) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['items']?.currentValue?.length && !changes['items'].previousValue?.length) {
      this.form = this.defaultForm();
      this.error = '';
      this.success = '';
    }
  }

  private defaultForm(): PrintOrderForm {
    return {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      addressLine1: '',
      addressLine2: '',
      city: '',
      postCode: '',
      country: 'JP',
      size: 'A4',
      quantity: 1,
      notes: '',
    };
  }

  submit() {
    if (!this.form.firstName || !this.form.lastName || !this.form.email ||
        !this.form.addressLine1 || !this.form.city || !this.form.postCode) {
      this.error = 'Please fill in all required fields.';
      return;
    }

    this.submitting = true;
    this.error = '';
    this.success = '';

    const payload = {
      images: this.items.map(i => ({
        job_id: i.job_id,
        presigned_url: i.presigned_url,
        template_key: i.template_key,
      })),
      shipping: {
        firstName: this.form.firstName,
        lastName: this.form.lastName,
        email: this.form.email,
        phone: this.form.phone,
        addressLine1: this.form.addressLine1,
        addressLine2: this.form.addressLine2,
        city: this.form.city,
        postCode: this.form.postCode,
        country: this.form.country,
      },
      size: this.form.size,
      quantity: this.form.quantity,
      notes: this.form.notes,
    };

    this.api.createOrder(payload).subscribe({
      next: (resp: any) => {
        this.submitting = false;
        this.success = 'Order saved! We\'ll be in touch shortly.';
        this.orderPlaced.emit(resp.order_id);
      },
      error: (err: any) => {
        this.submitting = false;
        this.error = err?.error?.error || 'Failed to place order. Please try again.';
      },
    });
  }
}
