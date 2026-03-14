import { Component, EventEmitter, Input, Output } from '@angular/core';
import { SampleEntry } from '../../models';

@Component({
  selector: 'app-sample-gallery',
  standalone: true,
  imports: [],
  templateUrl: './sample-gallery.component.html',
  styleUrl: './sample-gallery.component.css',
})
export class SampleGalleryComponent {
  @Input() samples: SampleEntry[] = [];
  @Input() loading = false;
  @Input() showDelete = false;
  @Output() sampleClicked = new EventEmitter<SampleEntry>();
  @Output() sampleDeleted = new EventEmitter<string>();

  onDelete(event: Event, sampleId: string) {
    event.stopPropagation();
    this.sampleDeleted.emit(sampleId);
  }
}
