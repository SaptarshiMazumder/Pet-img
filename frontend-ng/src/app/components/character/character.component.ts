import { Component, Input, Output, EventEmitter, HostListener, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-character',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './character.component.html',
  styleUrl: './character.component.css',
})
export class CharacterComponent implements OnInit, OnChanges {
  @Input() animation: 'idle' | 'happy' = 'idle';
  @Output() tapped = new EventEmitter<void>();

  readonly idleSrc = '/assets/animations/Idle2.gif';
  private readonly happyBase = '/assets/animations/Happy.gif';
  happySrc = this.happyBase;

  ngOnInit() {
    // Preload Happy.gif so it plays instantly on tap (no fetch delay)
    const img = new Image();
    img.src = this.happyBase;
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['animation']?.currentValue === 'happy') {
      // Force the GIF to restart from frame 1 by busting the cache key
      this.happySrc = `${this.happyBase}?t=${Date.now()}`;
    }
  }

  @HostListener('click')
  onClick() {
    this.tapped.emit();
  }
}
