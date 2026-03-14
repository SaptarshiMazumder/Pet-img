import { Component, EventEmitter, Input, Output } from '@angular/core';
import { JobEntry } from '../../models';

@Component({
  selector: 'app-job-queue',
  standalone: true,
  imports: [],
  templateUrl: './job-queue.component.html',
  styleUrl: './job-queue.component.css',
})
export class JobQueueComponent {
  @Input() jobs: JobEntry[] = [];
  @Input() templates: Record<string, any> = {};
  @Output() jobClicked = new EventEmitter<JobEntry>();
  @Output() jobRemoved = new EventEmitter<string>();

  onJobClick(job: JobEntry) {
    if (job.status === 'completed' && job.presigned_url) {
      this.jobClicked.emit(job);
    }
  }

  onRemove(event: Event, jobId: string) {
    event.stopPropagation();
    this.jobRemoved.emit(jobId);
  }

  templateName(key: string): string {
    return this.templates[key]?.name ?? key;
  }

  statusLabel(status: JobEntry['status']): string {
    const labels: Record<JobEntry['status'], string> = {
      pending: 'Queued',
      processing: 'Generating',
      fixing: 'Fixing',
      completed: 'Done',
      failed: 'Failed',
    };
    return labels[status] ?? status;
  }

  formatDuration(s: number): string {
    return s >= 60 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.round(s)}s`;
  }
}
