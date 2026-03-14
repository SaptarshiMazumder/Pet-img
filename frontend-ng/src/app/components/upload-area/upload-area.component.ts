import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-upload-area',
  standalone: true,
  imports: [],
  templateUrl: './upload-area.component.html',
  styleUrl: './upload-area.component.css',
})
export class UploadAreaComponent {
  @Input() previewUrl: string | null = null;
  @Output() fileSelected = new EventEmitter<File>();

  isDragOver = false;

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.[0]) this.fileSelected.emit(input.files[0]);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    const file = event.dataTransfer?.files[0];
    if (file) this.fileSelected.emit(file);
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave() {
    this.isDragOver = false;
  }
}
