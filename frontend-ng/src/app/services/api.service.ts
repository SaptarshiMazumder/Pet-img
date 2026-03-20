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

  getFrameCatalog(): Observable<{ categories: { name: string; variants: { color: string; preview_img_landscape: string; preview_img_portrait: string }[]; sizes: { [key: string]: { price: number } } }[] }> {
    return this.http.get<any>(`${this.base}/orders/catalog`);
  }

  createPayment(orderId: string, returnUrl: string): Observable<{ session_id: string; session_url: string; amount: number; total_jpy: number; currency: string }> {
    return this.http.post<any>(`${this.base}/orders/${orderId}/payment`, { return_url: returnUrl });
  }

  verifyPayment(orderId: string): Observable<{ success: boolean }> {
    return this.http.post<any>(`${this.base}/orders/${orderId}/payment/verify`, {});
  }
}
