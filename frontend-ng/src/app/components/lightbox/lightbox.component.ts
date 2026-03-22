import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { ExpandedItem } from '../../models';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-lightbox',
  standalone: true,
  imports: [],
  templateUrl: './lightbox.component.html',
  styleUrl: './lightbox.component.css',
})
export class LightboxComponent {
  protected readonly lang = inject(LanguageService);
  @Input() item: ExpandedItem | null = null;
  @Input() templates: Record<string, any> = {};
  @Output() closed = new EventEmitter<void>();
  @Output() orderClicked = new EventEmitter<void>();

  templateName(key: string): string {
    return this.lang.templateName(this.templates[key]) || key;
  }
}
