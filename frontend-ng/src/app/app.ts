import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from './services/api.service';

interface JobEntry {
  job_id: string;
  template_key: string;
  style_key: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  presigned_url?: string;
  positive_prompt?: string;
  seed?: number;
  error?: string;
  submitted_at: Date;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  styles: Record<string, any> = {};
  templates: Record<string, any> = {};
  styleKeys: string[] = [];
  templateKeys: string[] = [];

  selectedStyle = '';
  selectedTemplate = '';
  uploadedFile: File | null = null;
  previewUrl: string | null = null;
  isDragOver = false;

  submitting = false;
  errorMsg = '';

  jobs: JobEntry[] = [];
  private activePolls = new Set<string>();

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getStyles().subscribe(s => {
      this.styles = s;
      this.styleKeys = Object.keys(s);
      this.selectedStyle = this.styleKeys[0] || '';
    });
    this.api.getTemplates().subscribe(t => {
      for (const key of Object.keys(t)) {
        if (t[key].preview_url && !t[key].preview_url.startsWith('http')) {
          t[key].preview_url = this.api.assetUrl(t[key].preview_url);
        }
      }
      this.templates = t;
      this.templateKeys = Object.keys(t);
    });
  }

  ngOnDestroy() {
    this.activePolls.clear();
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
    return !!(this.uploadedFile && this.selectedTemplate && this.selectedStyle && !this.submitting);
  }

  generate() {
    if (!this.canGenerate) return;
    this.submitting = true;
    this.errorMsg = '';

    const form = new FormData();
    form.append('image', this.uploadedFile!);
    form.append('template_key', this.selectedTemplate);
    form.append('style_key', this.selectedStyle);

    this.api.submitGenerate(form).subscribe({
      next: (resp: any) => {
        const job_id = resp?.job_id ?? resp;
        this.submitting = false;
        this.jobs = [{
          job_id,
          template_key: this.selectedTemplate,
          style_key: this.selectedStyle,
          status: 'pending',
          submitted_at: new Date(),
        }, ...this.jobs];
        this.schedulePoll(job_id);
      },
      error: err => {
        this.submitting = false;
        this.errorMsg = err?.error?.error || err?.message || 'Failed to submit job.';
        console.error('submitGenerate error:', err);
      }
    });
  }

  private schedulePoll(jobId: string) {
    this.activePolls.add(jobId);
    setTimeout(() => this.doPoll(jobId), 2500);
  }

  private doPoll(jobId: string) {
    if (!this.activePolls.has(jobId)) return;

    this.api.getJobStatus(jobId).subscribe({
      next: (job: any) => {
        const idx = this.jobs.findIndex(j => j.job_id === jobId);
        if (idx !== -1) {
          this.jobs = [
            ...this.jobs.slice(0, idx),
            {
              ...this.jobs[idx],
              status: job.status,
              presigned_url: job.presigned_url ?? undefined,
              positive_prompt: job.positive_prompt ?? undefined,
              seed: job.seed ?? undefined,
              error: job.error ?? undefined,
            },
            ...this.jobs.slice(idx + 1),
          ];
        }
        if (job.status === 'completed' || job.status === 'failed') {
          this.activePolls.delete(jobId);
        } else {
          setTimeout(() => this.doPoll(jobId), 2500);
        }
      },
      error: () => {
        setTimeout(() => this.doPoll(jobId), 5000);
      }
    });
  }

  removeJob(jobId: string) {
    this.activePolls.delete(jobId);
    this.jobs = this.jobs.filter(j => j.job_id !== jobId);
  }

  templateName(key: string): string { return this.templates[key]?.name ?? key; }
  styleName(key: string): string { return this.styles[key]?.name ?? key; }
  templateIcon(i: number): string {
    return ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'][i % 8];
  }
}
