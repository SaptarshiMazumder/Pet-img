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
  @Input() templates: Record<string, any> = {};
  @Output() closed = new EventEmitter<void>();
  @Output() orderClicked = new EventEmitter<void>();

  templateName(key: string): string {
    return this.templates[key]?.name ?? key;
  }
}
