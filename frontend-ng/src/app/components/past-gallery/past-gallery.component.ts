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
  @Output() orderSelected = new EventEmitter<GalleryEntry[]>();
  @Output() refresh = new EventEmitter<void>();
  @Output() regenerateRequested = new EventEmitter<GalleryEntry>();

  private selectedIds = new Set<string>();

  templateName(key: string): string {
    return this.templates[key]?.name ?? key;
  }

  isSelected(job_id: string): boolean {
    return this.selectedIds.has(job_id);
  }

  toggleSelect(item: GalleryEntry, event: MouseEvent): void {
    event.stopPropagation();
    if (this.selectedIds.has(item.job_id)) {
      this.selectedIds.delete(item.job_id);
    } else {
      this.selectedIds.add(item.job_id);
    }
  }

  get selectedCount(): number {
    return this.selectedIds.size;
  }

  get selectedItems(): GalleryEntry[] {
    return this.gallery.filter(i => this.selectedIds.has(i.job_id));
  }

  openOrder(): void {
    this.orderSelected.emit(this.selectedItems);
  }
}
