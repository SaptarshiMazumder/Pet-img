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
  @Output() templateSelected = new EventEmitter<string>();

  @ViewChild('track') trackRef!: ElementRef<HTMLElement>;

  private icons = ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'];

  getIcon(i: number): string {
    return this.icons[i % this.icons.length];
  }

  scroll(dir: -1 | 1) {
    this.trackRef?.nativeElement.scrollBy({ left: dir * 220, behavior: 'smooth' });
  }
}
