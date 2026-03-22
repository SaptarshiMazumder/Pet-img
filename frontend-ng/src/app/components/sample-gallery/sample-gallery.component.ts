import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { SampleEntry } from '../../models';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-sample-gallery',
  standalone: true,
  imports: [],
  templateUrl: './sample-gallery.component.html',
  styleUrl: './sample-gallery.component.css',
})
export class SampleGalleryComponent {
  protected readonly lang = inject(LanguageService);
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
