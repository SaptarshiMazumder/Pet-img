import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = (window as any).__CONFIG__?.apiBase ?? 'http://localhost:5000';

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
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    return `${this.base}${path.startsWith('/') ? '' : '/'}${path}`;
  }

  placeOrder(payload: any): Observable<any> {
    return this.http.post<any>(`${this.base}/print/order`, payload);
  }

  createOrder(payload: any): Observable<{ order_id: string }> {
    return this.http.post<any>(`${this.base}/orders`, payload);
  }

  getOrders(): Observable<{ orders: any[] }> {
    return this.http.get<any>(`${this.base}/orders`);
  }

  updateOrder(orderId: string, payload: any): Observable<any> {
    return this.http.patch<any>(`${this.base}/orders/${orderId}`, payload);
  }

  getProducts(catalog = 'framed-posters'): Observable<any> {
    return this.http.get<any>(`${this.base}/print/products?catalog=${catalog}`);
  }

  getUserGenerations(): Observable<{ generations: any[] }> {
    return this.http.get<any>(`${this.base}/user/generations`);
  }

  deleteGeneration(jobId: string): Observable<{ success: boolean }> {
    return this.http.delete<any>(`${this.base}/user/generations/${jobId}`);
  }

  regenerateGeneration(jobId: string): Observable<{ job_id: string }> {
    return this.http.post<any>(`${this.base}/user/generations/${jobId}/regenerate`, {});
  }

  warm(): void {
    this.http.post(`${this.base}/warm`, {}).subscribe({ error: () => {} });
  }

  getSamples(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/samples`);
  }

  uploadSample(formData: FormData): Observable<any> {
    return this.http.post<any>(`${this.base}/samples`, formData);
  }

  deleteSample(sampleId: string): Observable<any> {
    return this.http.delete<any>(`${this.base}/samples/${sampleId}`);
  }

  detectGeo(): Observable<{ country: string }> {
    return this.http.get<{ country: string }>(`${this.base}/geo`);
  }

  getFrameCatalog(currency: string = 'JPY'): Observable<{ categories: { name: string; overlay_inset: number; variants: { color: string; preview_img_landscape: string; preview_img_portrait: string }[]; sizes: { [key: string]: { price: number } } }[]; currency: string }> {
    return this.http.get<any>(`${this.base}/orders/catalog?currency=${currency}`);
  }

  submitOrder(orderId: string, lang: string = 'en'): Observable<{ success: boolean }> {
    return this.http.post<any>(`${this.base}/orders/${orderId}/submit`, { lang });
  }

  // ── Credits & digital purchases ──────────────────────────────
  getCredits(): Observable<{ credits: number; packs: { pack_id: string; credits: number; price_usd: number; label: string }[]; payments_enabled: boolean }> {
    return this.http.get<any>(`${this.base}/credits`);
  }

  createCreditCheckout(packId: string, returnUrl?: string): Observable<{ checkout_url: string; session_id: string }> {
    return this.http.post<any>(`${this.base}/credits/checkout`, { pack_id: packId, return_url: returnUrl });
  }

  unlockGeneration(jobId: string): Observable<{ unlocked: boolean; credits_remaining: number; download_url: string | null }> {
    return this.http.post<any>(`${this.base}/user/generations/${jobId}/unlock`, {});
  }

  getDownloadUrl(jobId: string): Observable<{ download_url: string }> {
    return this.http.get<any>(`${this.base}/user/generations/${jobId}/download`);
  }
}
