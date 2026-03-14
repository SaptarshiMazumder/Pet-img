import { Component, EventEmitter, Input, Output } from '@angular/core';
import { GalleryEntry } from '../../models';

@Component({
  selector: 'app-past-gallery',
  standalone: true,
  imports: [],
  templateUrl: './past-gallery.component.html',
  styleUrl: './past-gallery.component.css',
})
export class PastGalleryComponent {
  @Input() gallery: GalleryEntry[] = [];
  @Input() loading = false;
  @Input() templates: Record<string, any> = {};
  @Output() itemClicked = new EventEmitter<GalleryEntry>();
  @Output() refresh = new EventEmitter<void>();

  templateName(key: string): string {
    return this.templates[key]?.name ?? key;
  }
}
