import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ExpandedItem } from '../../models';

@Component({
  selector: 'app-lightbox',
  standalone: true,
  imports: [],
  templateUrl: './lightbox.component.html',
  styleUrl: './lightbox.component.css',
})
export class LightboxComponent {
  @Input() item: ExpandedItem | null = null;
  @Output() closed = new EventEmitter<void>();
}
