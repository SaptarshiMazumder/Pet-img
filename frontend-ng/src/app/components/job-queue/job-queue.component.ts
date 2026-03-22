import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { JobEntry } from '../../models';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-job-queue',
  standalone: true,
  imports: [],
  templateUrl: './job-queue.component.html',
  styleUrl: './job-queue.component.css',
})
export class JobQueueComponent {
  protected readonly lang = inject(LanguageService);
  @Input() jobs: JobEntry[] = [];
  @Input() templates: Record<string, any> = {};
  @Output() jobClicked = new EventEmitter<JobEntry>();
  @Output() jobRemoved = new EventEmitter<string>();
  @Output() jobRegenerate = new EventEmitter<JobEntry>();

  onJobClick(job: JobEntry) {
    if (job.status === 'completed' && job.presigned_url) {
      this.jobClicked.emit(job);
    }
  }

  onRemove(event: Event, jobId: string) {
    event.stopPropagation();
    this.jobRemoved.emit(jobId);
  }

  onRegen(event: Event, job: JobEntry) {
    event.stopPropagation();
    if (confirm(this.lang.t().confirm.regenerate)) {
      this.jobRegenerate.emit(job);
    }
  }

  templateName(key: string): string {
    return this.lang.templateName(this.templates[key]) || key;
  }

  statusLabel(status: JobEntry['status']): string {
    return this.lang.t().queue.status[status] ?? status;
  }

  formatDuration(s: number): string {
    return s >= 60 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.round(s)}s`;
  }
}
