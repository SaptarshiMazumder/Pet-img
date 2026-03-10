import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = 'http://localhost:5000';

  constructor(private http: HttpClient) {}

  getStyles(): Observable<Record<string, { name: string; trigger_word: string }>> {
    return this.http.get<any>(`${this.base}/styles`);
  }

  getTemplates(): Observable<Record<string, { name: string; preview_url: string; mood: string; environment: string }>> {
    return this.http.get<any>(`${this.base}/templates`);
  }

  submitGenerate(formData: FormData): Observable<{ job_id: string }> {
    return this.http.post<any>(`${this.base}/generate`, formData);
  }

  getJobStatus(jobId: string): Observable<any> {
    return this.http.get<any>(`${this.base}/job/${jobId}`);
  }

  assetUrl(path: string): string {
    return `${this.base}${path.startsWith('/') ? '' : '/'}${path}`;
  }
}
