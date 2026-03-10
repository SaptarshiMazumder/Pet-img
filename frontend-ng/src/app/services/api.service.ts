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

  generate(formData: FormData): Observable<any> {
    return this.http.post<any>(`${this.base}/generate`, formData);
  }

  r2ImageUrl(key: string): string {
    return `${this.base}/r2-image?key=${encodeURIComponent(key)}`;
  }

  assetUrl(path: string): string {
    return `${this.base}${path.startsWith('/') ? '' : '/'}${path}`;
  }
}
