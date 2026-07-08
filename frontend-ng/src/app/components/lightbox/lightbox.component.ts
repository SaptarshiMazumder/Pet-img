import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { ExpandedItem } from '../../models';
import { LanguageService } from '../../services/language.service';
import { PRINTS_ENABLED } from '../../config';

@Component({
  selector: 'app-lightbox',
  standalone: true,
  imports: [],
  templateUrl: './lightbox.component.html',
  styleUrl: './lightbox.component.css',
})
export class LightboxComponent {
  protected readonly lang = inject(LanguageService);
  protected readonly printsEnabled = PRINTS_ENABLED;
  @Input() item: ExpandedItem | null = null;
  @Input() templates: Record<string, any> = {};
  @Input() unlocking = false;
  @Output() closed = new EventEmitter<void>();
  @Output() orderClicked = new EventEmitter<void>();
  @Output() unlockClicked = new EventEmitter<void>();
  @Output() downloadClicked = new EventEmitter<void>();

  templateName(key: string): string {
    return this.lang.templateName(this.templates[key]) || key;
  }

  ja(): boolean {
    return this.lang.lang() === 'ja';
  }
}
