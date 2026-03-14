import { Component, EventEmitter, Input, Output } from '@angular/core';

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

  private icons = ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'];

  getIcon(i: number): string {
    return this.icons[i % this.icons.length];
  }
}
