import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-credit-recharge-modal',
  standalone: true,
  templateUrl: './credit-recharge-modal.component.html',
  styleUrl: './credit-recharge-modal.component.css',
})
export class CreditRechargeModalComponent {
  readonly lang = inject(LanguageService);

  @Input() open = false;
  @Input() packLine = '';
  @Input() balanceLine = '';
  @Input() submitting = false;
  @Input() errorMessage: string | null = null;

  @Output() closed = new EventEmitter<void>();
  @Output() checkout = new EventEmitter<void>();

  close() {
    this.closed.emit();
  }
}
