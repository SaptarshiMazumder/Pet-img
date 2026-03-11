import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { User } from 'firebase/auth';
import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';

interface GalleryEntry {
  job_id: string;
  template_key: string;
  style_key: string;
  presigned_url: string | null;
  seed: number | null;
  created_at: string | null;
}

interface OrderForm {
  firstName: string;
  lastName: string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  postCode: string;
  country: string;
  email: string;
  phone: string;
  product_uid: string;
  quantity: number;
  order_type: 'draft' | 'order';
}

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
  imports: [CommonModule, FormsModule],
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
  dryRun = false;

  jobs: JobEntry[] = [];
  private activePolls = new Set<string>();

  orderModalJob: JobEntry | null = null;
  orderForm: OrderForm = this._defaultOrderForm();
  orderSubmitting = false;
  orderError = '';
  orderSuccess = '';

  products: { uid: string; label: string }[] = [];
  productsLoading = false;

  currentUser: User | null = null;
  gallery: GalleryEntry[] = [];
  galleryLoading = false;
  private authSub!: Subscription;

  expandedItem: { job_id: string; presigned_url: string; positive_prompt?: string; template_key: string; style_key: string } | null = null;

  constructor(private api: ApiService, private auth: AuthService) {}

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
    this.authSub = this.auth.user$.subscribe(user => {
      this.currentUser = user;
      if (user) {
        this.loadGallery();
      } else {
        this.gallery = [];
      }
    });
  }

  ngOnDestroy() {
    this.activePolls.clear();
    this.authSub?.unsubscribe();
  }

  signIn() { this.auth.signInWithGoogle().catch(err => console.error('Sign-in error', err)); }
  signOut() { this.auth.signOut(); }

  loadGallery() {
    this.galleryLoading = true;
    this.api.getUserGenerations().subscribe({
      next: resp => { this.gallery = resp.generations; this.galleryLoading = false; },
      error: () => { this.galleryLoading = false; },
    });
  }

  openExpandFromJob(job: JobEntry) {
    if (!job.presigned_url) return;
    this.expandedItem = { job_id: job.job_id, presigned_url: job.presigned_url, positive_prompt: job.positive_prompt, template_key: job.template_key, style_key: job.style_key };
  }

  openExpandFromGallery(item: GalleryEntry) {
    if (!item.presigned_url) return;
    this.expandedItem = { job_id: item.job_id, presigned_url: item.presigned_url, template_key: item.template_key, style_key: item.style_key };
  }

  closeExpand() { this.expandedItem = null; }

  orderFromExpand() {
    if (!this.expandedItem) return;
    const item = this.expandedItem;
    this.closeExpand();
    this.openOrderModal({ job_id: item.job_id, template_key: item.template_key, style_key: item.style_key, status: 'completed', presigned_url: item.presigned_url, submitted_at: new Date() });
  }

  openOrderModalFromGallery(item: GalleryEntry) {
    this.openOrderModal({
      job_id: item.job_id,
      template_key: item.template_key,
      style_key: item.style_key,
      status: 'completed',
      presigned_url: item.presigned_url ?? undefined,
      submitted_at: item.created_at ? new Date(item.created_at) : new Date(),
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
    form.append('dry_run', String(this.dryRun));

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
          if (job.status === 'completed' && this.currentUser) {
            setTimeout(() => this.loadGallery(), 1500);
          }
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

  private _defaultOrderForm(): OrderForm {
    return {
      firstName: '',
      lastName: '',
      addressLine1: '',
      addressLine2: '',
      city: '',
      postCode: '',
      country: 'JP',
      email: '',
      phone: '',
      product_uid: '',
      quantity: 1,
      order_type: 'draft',
    };
  }

  openOrderModal(job: JobEntry) {
    this.orderModalJob = job;
    this.orderForm = this._defaultOrderForm();
    this.orderError = '';
    this.orderSuccess = '';
    if (this.products.length === 0) {
      this.productsLoading = true;
      this.api.getProducts().subscribe({
        next: (resp: any) => {
          const list: any[] = resp?.products ?? resp?.data ?? (Array.isArray(resp) ? resp : []);
          this.products = list.map((p: any) => ({
            uid: p.productUid ?? p.uid ?? p.product_uid ?? '',
            label: p.title ?? p.name ?? this._uidLabel(p.productUid ?? p.uid ?? ''),
          })).filter(p => p.uid);
          if (this.products.length > 0) {
            this.orderForm.product_uid = this.products[0].uid;
          }
          this.productsLoading = false;
        },
        error: () => { this.productsLoading = false; },
      });
    }
  }

  private _uidLabel(uid: string): string {
    const m = uid.match(/pf_([\d]+x[\d]+-mm)/);
    const size = m ? m[1].replace(/-mm$/, ' mm').replace('x', ' × ') : '';
    const pt = uid.match(/pt_([\w-]+)/);
    const paper = pt ? pt[1].replace(/-/g, ' ') : '';
    return [size, paper].filter(Boolean).join(' — ') || uid;
  }

  closeOrderModal() {
    this.orderModalJob = null;
  }

  submitOrder() {
    if (!this.orderModalJob?.presigned_url) return;
    if (!this.orderForm.product_uid) { this.orderError = 'Please select a product.'; return; }
    this.orderSubmitting = true;
    this.orderError = '';
    this.orderSuccess = '';

    const f = this.orderForm;
    const payload = {
      image_url: this.orderModalJob.presigned_url,
      product_uid: f.product_uid,
      quantity: f.quantity,
      order_type: f.order_type,
      shipping_address: {
        firstName: f.firstName,
        lastName: f.lastName,
        addressLine1: f.addressLine1,
        addressLine2: f.addressLine2,
        city: f.city,
        postCode: f.postCode,
        country: f.country,
        email: f.email,
        phone: f.phone,
      },
    };

    this.api.placeOrder(payload).subscribe({
      next: (resp: any) => {
        this.orderSuccess = 'Order placed! Order ID: ' + resp.order_id;
        this.orderSubmitting = false;
      },
      error: (err: any) => {
        this.orderError = err?.error?.error || 'Failed to place order.';
        this.orderSubmitting = false;
      },
    });
  }

  templateName(key: string): string { return this.templates[key]?.name ?? key; }
  styleName(key: string): string { return this.styles[key]?.name ?? key; }
  templateIcon(i: number): string {
    return ['⛩', '🌸', '🗡', '🏯', '🌊', '🌙', '📜', '🏮'][i % 8];
  }
}
