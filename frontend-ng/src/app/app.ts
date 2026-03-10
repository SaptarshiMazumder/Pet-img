import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from './services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  styles: Record<string, any> = {};
  templates: Record<string, any> = {};
  styleKeys: string[] = [];
  templateKeys: string[] = [];

  selectedStyle = '';
  selectedTemplate = '';
  uploadedFile: File | null = null;
  previewUrl: string | null = null;
  isDragOver = false;

  generating = false;
  errorMsg = '';
  result: any = null;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getStyles().subscribe(s => {
      this.styles = s;
      this.styleKeys = Object.keys(s);
      this.selectedStyle = this.styleKeys[0] || '';
    });
    this.api.getTemplates().subscribe(t => {
      // Prefix Flask base URL so preview images resolve correctly
      for (const key of Object.keys(t)) {
        if (t[key].preview_url && !t[key].preview_url.startsWith('http')) {
          t[key].preview_url = this.api.assetUrl(t[key].preview_url);
        }
      }
      this.templates = t;
      this.templateKeys = Object.keys(t);
    });
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.[0]) this.setFile(input.files[0]);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    const file = event.dataTransfer?.files[0];
    if (file) this.setFile(file);
  }

  onDragOver(event: DragEvent) { event.preventDefault(); this.isDragOver = true; }
  onDragLeave() { this.isDragOver = false; }

  setFile(file: File) {
    this.uploadedFile = file;
    const reader = new FileReader();
    reader.onload = e => this.previewUrl = e.target?.result as string;
    reader.readAsDataURL(file);
  }

  selectStyle(key: string) { this.selectedStyle = key; }
  selectTemplate(key: string) { this.selectedTemplate = key; }

  get canGenerate(): boolean {
    return !!(this.uploadedFile && this.selectedTemplate && this.selectedStyle && !this.generating);
  }

  generate() {
    if (!this.canGenerate) return;
    this.generating = true;
    this.errorMsg = '';
    this.result = null;

    const form = new FormData();
    form.append('image', this.uploadedFile!);
    form.append('template_key', this.selectedTemplate);
    form.append('style_key', this.selectedStyle);

    this.api.generate(form).subscribe({
      next: data => {
        this.generating = false;
        if (data.error) { this.errorMsg = data.error; return; }
        const img0 = data.images?.[0];
        if (img0?.url?.startsWith('http')) {
          data.result_image_url = img0.url;
        } else if (img0?.key) {
          data.result_image_url = this.api.r2ImageUrl(img0.key);
        }
        this.result = data;
      },
      error: err => {
        this.generating = false;
        this.errorMsg = err.error?.error || 'Request failed';
      }
    });
  }

  clearResult() {
    this.result = null;
    this.errorMsg = '';
  }

  onImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
    this.errorMsg = 'Image failed to load. URL tried: ' + (this.result?.result_image_url ?? 'none');
  }

  templateIcon(i: number): string {
    return ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'][i % 8];
  }
}
