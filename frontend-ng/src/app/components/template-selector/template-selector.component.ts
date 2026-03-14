import { Component, EventEmitter, Input, Output, ViewChild, ElementRef } from '@angular/core';

@Component({
  selector: 'app-template-selector',
  standalone: true,
  imports: [],
  templateUrl: './template-selector.component.html',
  styleUrl: './template-selector.component.css',
})
export class TemplateSelectorComponent {
  @Input() templates: Record<string, any> = {};
  @Input() templateKeys: string[] = [];
  @Input() selectedTemplate = '';
  @Input() sectionTitle = 'Explore Styles';
  @Input() previewOnly = false;
  @Output() templateSelected = new EventEmitter<string>();

  @ViewChild('carouselTrack') carouselTrackRef!: ElementRef<HTMLElement>;

  showAllModal = false;
  previewImage: string | null = null;

  private icons = ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'];

  private scrollToSelected(key?: string) {
    const target = key ?? this.selectedTemplate;
    const idx = this.templateKeys.indexOf(target);
    if (idx < 0) return;
    const track = this.carouselTrackRef?.nativeElement;
    if (!track || !track.children[idx]) return;
    (track.children[idx] as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }

  getIcon(i: number): string {
    return this.icons[i % this.icons.length];
  }

  selectFromModal(key: string) {
    if (this.previewOnly) {
      const url = this.templates[key]?.preview_url;
      if (url) this.previewImage = url;
    } else {
      this.templateSelected.emit(key);
      this.showAllModal = false;
      setTimeout(() => this.scrollToSelected(key), 50);
    }
  }

  closePreview() {
    this.previewImage = null;
  }
}
