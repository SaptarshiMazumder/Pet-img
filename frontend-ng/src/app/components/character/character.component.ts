import { Component, Input, Output, EventEmitter, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-character',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './character.component.html',
  styleUrl: './character.component.css',
})
export class CharacterComponent implements OnInit {
  @Input() animation: 'idle' | 'happy' = 'idle';
  @Output() tapped = new EventEmitter<void>();

  readonly idleSrc = '/assets/animations/Idle2.gif';
  readonly happySrc = '/assets/animations/Happy.gif';

  ngOnInit() {
    // Preload Happy.gif so it plays instantly on tap (no fetch delay)
    const img = new Image();
    img.src = this.happySrc;
  }

  @HostListener('click')
  onClick() {
    this.tapped.emit();
  }
}
