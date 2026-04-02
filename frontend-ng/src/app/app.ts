import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { User } from './services/auth.service';
import { ApiService } from './services/api.service';
import { AuthService } from './services/auth.service';
import { LanguageService } from './services/language.service';
import { CharacterComponent } from './components/character/character.component';
import { UploadAreaComponent } from './components/upload-area/upload-area.component';
import { TemplateSelectorComponent } from './components/template-selector/template-selector.component';
import { JobQueueComponent } from './components/job-queue/job-queue.component';
import { SampleGalleryComponent } from './components/sample-gallery/sample-gallery.component';
import { PastGalleryComponent } from './components/past-gallery/past-gallery.component';
import { LightboxComponent } from './components/lightbox/lightbox.component';
import { DownloadModalComponent, PricingInfo } from './components/download-modal/download-modal.component';
import { OrderModalComponent } from './components/order-modal/order-modal.component';
import { OrderFlowComponent } from './components/order-flow/order-flow.component';
import { OrdersPageComponent } from './components/orders-page/orders-page.component';
import { AuthModalComponent } from './components/auth-modal/auth-modal.component';
import { CreditRechargeModalComponent } from './components/credit-recharge-modal/credit-recharge-modal.component';
import { GalleryEntry, OrderForm, JobEntry, ExpandedItem, SampleEntry, Order } from './models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    CharacterComponent,
    UploadAreaComponent,
    TemplateSelectorComponent,
    JobQueueComponent,
    SampleGalleryComponent,
    PastGalleryComponent,
    LightboxComponent,
    DownloadModalComponent,
    OrderModalComponent,
    OrderFlowComponent,
    OrdersPageComponent,
    AuthModalComponent,
    CreditRechargeModalComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  // ── Templates ──────────────────────────────────────────────
  templates: Record<string, any> = {};
  templateKeys: string[] = [];
  selectedTemplate = '';

  // ── Upload ─────────────────────────────────────────────────
  uploadedFile: File | null = null;
  previewUrl: string | null = null;

  // ── Aspect ratio ───────────────────────────────────────────
  // 4:5 portrait matches F-series frames well; landscape is the same rotated.
  readonly ratioOptions = [
    { label: 'Portrait',  w: 832,  h: 1040 },
    { label: 'Landscape', w: 1040, h: 832  },
  ];
  selectedRatio = this.ratioOptions[0]; // default: portrait

  // ── Generate ───────────────────────────────────────────────
  submitting = false;
  errorMsg = '';
  dryRun = false;
  jobs: JobEntry[] = [];
  private activePolls = new Set<string>();

  // ── USO mode ───────────────────────────────────────────────
  generateMode: 'zturbo' | 'uso' = 'zturbo';
  readonly usoRatioOptions = [
    { label: 'Portrait',  w: 896,  h: 1152 },
    { label: 'Landscape', w: 1152, h: 896  },
  ];
  usoSelectedRatio = this.usoRatioOptions[0];
  readonly generateModes: { value: 'zturbo' | 'uso'; label: string }[] =
    (window as any).__CONFIG__?.generateModes ?? [
      { value: 'zturbo', label: 'Japanese' },
      { value: 'uso',    label: 'Oil Painting' },
    ];
  usoSubjectFile: File | null = null;
  usoSubjectPreview: string | null = null;
  usoTemplates: Record<string, any> = {};
  usoTemplateKeys: string[] = [];
  selectedUsoTemplate = '';

  setUsoSubjectFile(file: File) {
    this.usoSubjectFile = file;
    const reader = new FileReader();
    reader.onload = (e) => (this.usoSubjectPreview = e.target?.result as string);
    reader.readAsDataURL(file);
  }

  get canGenerateUso(): boolean {
    return !!(
      this.usoSubjectFile &&
      this.selectedUsoTemplate &&
      !this.submitting &&
      this.currentUser &&
      this.creditsLoadState === 'ok' &&
      this.creditBalance !== null &&
      this.creditBalance > 0
    );
  }

  generateUso() {
    if (!this.canGenerateUso) return;
    this.submitting = true;
    this.errorMsg = '';

    const form = new FormData();
    form.append('subject_image', this.usoSubjectFile!);
    form.append('template_key', this.selectedUsoTemplate);
    form.append('width', String(this.usoSelectedRatio.w));
    form.append('height', String(this.usoSelectedRatio.h));
    form.append('orientation', this.usoSelectedRatio.label.toLowerCase());

    this.api.submitUsoGenerate(form).subscribe({
      next: (resp: any) => {
        const job_id = resp?.job_id ?? resp;
        if (resp?.credits_remaining !== undefined) this.creditBalance = resp.credits_remaining;
        this.submitting = false;
        this.jobs = [
          {
            job_id,
            template_key: 'uso',
            style_key: 'uso',
            status: 'pending',
            submitted_at: new Date(),
          },
          ...this.jobs,
        ];
        this.schedulePoll(job_id);
      },
      error: (err) => {
        this.submitting = false;
        if (err?.status === 402) {
          this.creditBalance = 0;
          this.errorMsg = err?.error?.error || 'No credits remaining.';
        } else {
          this.errorMsg = err?.error?.error || err?.message || 'Failed to submit USO job.';
        }
      },
    });
  }

  // ── Credits ────────────────────────────────────────────────
  creditBalance: number | null = null;
  /** Credits required for high-res download (from API; default 10). */
  downloadCreditCost = 10;
  /** Tracks loading / error so we never show a stuck ellipsis placeholder. */
  creditsLoadState: 'idle' | 'loading' | 'ok' | 'error' = 'idle';
  rechargePrice: {
    label: string;
    amount: number;
    currency: string;
    credits: number;
    locale: string;
  } | null = null;

  showRechargeModal = false;
  rechargeSubmitting = false;
  rechargeCheckoutError: string | null = null;

  /** Fiat equivalent of current credits (for recharge modal). */
  private formatBalanceMoneyValue(): string {
    if (this.creditBalance === null || !this.rechargePrice?.credits) {
      return '';
    }
    const per = this.rechargePrice.amount / this.rechargePrice.credits;
    const v = this.creditBalance * per;
    try {
      return new Intl.NumberFormat(this.rechargePrice.locale || 'en-US', {
        style: 'currency',
        currency: this.rechargePrice.currency,
      }).format(v);
    } catch {
      return v.toFixed(2);
    }
  }

  /** Header pill: credit count only (no currency). */
  get headerCreditsDisplay(): string {
    if (this.creditsLoadState === 'loading') return '…';
    if (this.creditsLoadState === 'error') return '—';
    if (this.creditBalance === null) return '…';
    return String(this.creditBalance);
  }

  /** Buy modal pack row: credits + price (e.g. "25 credits · ¥1,000"). */
  get rechargePackLine(): string {
    if (!this.rechargePrice) return '';
    const c = String(this.rechargePrice.credits ?? 25);
    return this.lang.t().credits.packLineTemplate
      .replace('{{count}}', c)
      .replace('{{price}}', this.rechargePrice.label);
  }

  /** Buy modal balance row: credits + fiat equivalent. */
  get rechargeBalanceLine(): string {
    if (this.creditsLoadState === 'loading') return '…';
    if (this.creditsLoadState === 'error') return '—';
    if (this.creditBalance === null) return '…';
    const count = String(this.creditBalance);
    const money = this.formatBalanceMoneyValue() || '—';
    return this.lang.t().credits.balanceCreditsMoney
      .replace('{{count}}', count)
      .replace('{{money}}', money);
  }

  loadCredits() {
    if (!this.currentUser) return;
    this.creditsLoadState = 'loading';
    this.api.getRechargePrice().subscribe({
      next: (p) => {
        this.rechargePrice = p;
      },
      error: () => {},
    });
    this.api.getCredits().subscribe({
      next: (r) => {
        this.creditBalance = r.credits;
        if (r.download_credit_cost != null && r.download_credit_cost > 0) {
          this.downloadCreditCost = r.download_credit_cost;
        }
        this.creditsLoadState = 'ok';
      },
      error: () => {
        this.creditBalance = null;
        this.creditsLoadState = 'error';
      },
    });
  }

  openRechargeModal() {
    this.rechargeCheckoutError = null;
    if (!this.rechargePrice) {
      this.api.getRechargePrice().subscribe({
        next: (p) => {
          this.rechargePrice = p;
          this.showRechargeModal = true;
        },
        error: () => {
          this.showRechargeModal = true;
          this.rechargeCheckoutError = this.lang.t().credits.loadFailed;
        },
      });
    } else {
      this.showRechargeModal = true;
    }
  }

  closeRechargeModal() {
    this.showRechargeModal = false;
    this.rechargeSubmitting = false;
  }

  startCreditCheckout() {
    this.rechargeSubmitting = true;
    this.rechargeCheckoutError = null;
    this.api.createCreditCheckoutSession().subscribe({
      next: (r) => {
        if (r?.url) {
          window.location.href = r.url;
        } else {
          this.rechargeSubmitting = false;
          this.rechargeCheckoutError = this.lang.t().credits.checkoutFailed;
        }
      },
      error: (err: any) => {
        this.rechargeSubmitting = false;
        const code = err?.error?.error;
        if (code === 'payment_not_configured') {
          this.rechargeCheckoutError = this.lang.t().credits.paymentNotConfigured;
        } else {
          this.rechargeCheckoutError =
            err?.error?.detail || err?.error?.error || this.lang.t().credits.checkoutFailed;
        }
      },
    });
  }

  // ── Auth / User ────────────────────────────────────────────
  currentUser: User | null = null;
  private authSub!: Subscription;

  // ── Gallery (past generations) ──────────────────────────────
  gallery: GalleryEntry[] = [];
  galleryLoading = false;

  // ── Samples ────────────────────────────────────────────────
  samples: SampleEntry[] = [];
  samplesLoading = false;
  sampleUploadFile: File | null = null;
  samplePreviewUrl: string | null = null;
  sampleUploading = false;
  sampleError = '';

  // ── Download modal ─────────────────────────────────────────
  downloadImageUrl: string | null = null;
  /** Generation id for credit-based download; null for samples or unknown. */
  downloadJobId: string | null = null;

  downloadLatest() {
    const completed = this.jobs.find((j) => j.status === 'completed' && j.presigned_url);
    if (completed?.presigned_url) {
      this.downloadImageUrl = completed.presigned_url;
      this.downloadJobId = completed.job_id;
      return;
    }
    const fromGallery = this.gallery.find((g) => g.presigned_url);
    if (fromGallery?.presigned_url) {
      this.downloadImageUrl = fromGallery.presigned_url;
      this.downloadJobId = fromGallery.job_id;
    }
  }

  closeDownloadModal() {
    this.downloadImageUrl = null;
    this.downloadJobId = null;
  }

  onCreditsUpdatedFromDownload(balance: number) {
    this.creditBalance = balance;
    // Balance already reflects deduction; cost unchanged
  }

  onPayClicked(pricing: PricingInfo) {
    // Payment integration to be wired up
    console.log('[download] pay clicked', pricing);
  }

  // ── Lightbox ───────────────────────────────────────────────
  expandedItem: ExpandedItem | null = null;

  // ── Order flow ─────────────────────────────────────────────
  orderFlowItems: GalleryEntry[] = [];
  editingOrder: Order | null = null;
  private _orderFlowOrigin: typeof this.activeTab = 'gallery';

  openOrderFlow(items: GalleryEntry[]) {
    this._orderFlowOrigin = this.activeTab;
    this.editingOrder = null;
    this.orderFlowItems = items;
    this.activeTab = 'order';
  }

  openOrderForEdit(order: Order) {
    const item = order.items[0];
    if (!item) return;
    this._orderFlowOrigin = this.activeTab;
    this.editingOrder = order;
    this.orderFlowItems = [{
      job_id: item.job_id,
      template_key: item.template_key || '',
      style_key: '',
      presigned_url: item.presigned_url,
      source_url: null,
      seed: null,
      created_at: order.created_at,
      orientation: (item.orientation as 'portrait' | 'landscape') ?? undefined,
    }];
    this.activeTab = 'order';
  }

  closeOrderFlow() {
    this.orderFlowItems = [];
    this.editingOrder = null;
    this.activeTab = this._orderFlowOrigin;
  }

  onOrderPlaced() {
    this.orderFlowItems = [];
    this.editingOrder = null;
    this.activeTab = 'orders';
    this.loadOrders();
  }

  // ── Orders page ─────────────────────────────────────────────
  orders: Order[] = [];
  ordersLoading = false;

  loadOrders() {
    this.ordersLoading = true;
    this.api.getOrders().subscribe({
      next: (resp) => { this.orders = resp.orders; this.ordersLoading = false; },
      error: () => { this.ordersLoading = false; },
    });
  }

  // ── Order modal ────────────────────────────────────────────
  orderModalJob: JobEntry | null = null;
  orderSubmitting = false;
  orderError = '';
  orderSuccess = '';
  products: { uid: string; label: string }[] = [];
  productsLoading = false;

  // ── Navigation ─────────────────────────────────────────────
  activeTab: 'generate' | 'samples' | 'upload' | 'orders' | 'gallery' | 'order' = 'samples';
  characterAnimation: 'idle' | 'happy' = 'idle';
  fabRotating = false;
  catMenuOpen = false;
  headerMenuOpen = false;
  private happyTimeout: ReturnType<typeof setTimeout> | null = null;
  constructor(
    private api: ApiService,
    private auth: AuthService,
    readonly lang: LanguageService,
  ) {}

  ngOnInit() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('recharge') === 'success') {
      params.delete('recharge');
      params.delete('session_id');
      const q = params.toString();
      window.history.replaceState(
        {},
        '',
        window.location.pathname + (q ? '?' + q : '') + window.location.hash,
      );
    }

    this.api.warm();
    this.api.getTemplates().subscribe((t) => {
      this.templates = t;
      this.templateKeys = Object.keys(t);
    });
    this.api.getUsoTemplates().subscribe((t) => {
      this.usoTemplates = t;
      this.usoTemplateKeys = Object.keys(t);
    });
    this.authSub = this.auth.user$.subscribe((user) => {
      this.currentUser = user;
      if (user) {
        this.loadGallery();
        this.loadSamples();
        this.loadCredits();
      } else {
        this.gallery = [];
        this.samples = [];
        this.creditBalance = null;
        this.downloadCreditCost = 10;
        this.creditsLoadState = 'idle';
        this.showRechargeModal = false;
      }
    });
    this.loadSamples();

  }

  ngOnDestroy() {
    this.activePolls.clear();
    this.authSub?.unsubscribe();
    if (this.happyTimeout) clearTimeout(this.happyTimeout);
  }

  // ── Auth ───────────────────────────────────────────────────
  showAuthModal = false;

  signIn() {
    this.showAuthModal = true;
    this.headerMenuOpen = false;
  }

  signOut() {
    this.auth.signOut();
  }

  // ── Gallery ────────────────────────────────────────────────
  loadGallery() {
    this.galleryLoading = true;
    this.api.getUserGenerations().subscribe({
      next: (resp) => {
        this.gallery = resp.generations;
        this.galleryLoading = false;
      },
      error: () => {
        this.galleryLoading = false;
      },
    });
  }

  // ── Upload ─────────────────────────────────────────────────
  setFile(file: File) {
    this.uploadedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => (this.previewUrl = e.target?.result as string);
    reader.readAsDataURL(file);
  }

  selectTemplate(key: string) {
    this.selectedTemplate = key;
  }

  onGalleryStyleSelected(key: string) {
    this.selectTemplate(key);
    this.switchTab('generate');
  }

  get canGenerate(): boolean {
    return !!(
      this.uploadedFile &&
      this.selectedTemplate &&
      !this.submitting &&
      this.currentUser &&
      this.creditsLoadState === 'ok' &&
      this.creditBalance !== null &&
      this.creditBalance > 0
    );
  }

  get canOrderPrint(): boolean {
    const completed = this.jobs.find((j) => j.status === 'completed' && j.presigned_url);
    if (completed) return true;
    const fromGallery = this.gallery.find((g) => g.presigned_url);
    return !!fromGallery;
  }

  openOrderFromLatest() {
    const completed = this.jobs.find((j) => j.status === 'completed' && j.presigned_url);
    if (completed) {
      this.openOrderFlow([{
        job_id: completed.job_id,
        template_key: completed.template_key,
        style_key: completed.style_key,
        presigned_url: completed.presigned_url ?? null,
        source_url: null,
        seed: null,
        created_at: null,
        orientation: completed.orientation,
      }]);
      return;
    }
    const fromGallery = this.gallery.find((g) => g.presigned_url);
    if (fromGallery) {
      this.openOrderFlow([fromGallery]);
    }
  }

  // ── Generate ───────────────────────────────────────────────
  generate() {
    if (!this.canGenerate) return;
    this.submitting = true;
    this.errorMsg = '';

    const form = new FormData();
    form.append('image', this.uploadedFile!);
    form.append('template_key', this.selectedTemplate);
    form.append('style_key', 'inkwash');
    form.append('dry_run', String(this.dryRun));
    form.append('width', String(this.selectedRatio.w));
    form.append('height', String(this.selectedRatio.h));
    form.append('orientation', this.selectedRatio.label.toLowerCase() as 'portrait' | 'landscape');

    this.api.submitGenerate(form).subscribe({
      next: (resp: any) => {
        const job_id = resp?.job_id ?? resp;
        if (resp?.credits_remaining !== undefined) this.creditBalance = resp.credits_remaining;
        this.submitting = false;
        this.jobs = [
          {
            job_id,
            template_key: this.selectedTemplate,
            style_key: 'inkwash',
            status: 'pending',
            submitted_at: new Date(),
            orientation: this.selectedRatio.label.toLowerCase() as 'portrait' | 'landscape',
          },
          ...this.jobs,
        ];
        this.schedulePoll(job_id);
      },
      error: (err) => {
        this.submitting = false;
        if (err?.status === 402) {
          this.creditBalance = 0;
          this.errorMsg = err?.error?.error || 'No credits remaining.';
        } else {
          this.errorMsg = err?.error?.error || err?.message || 'Failed to submit job.';
        }
      },
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
        const idx = this.jobs.findIndex((j) => j.job_id === jobId);
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
              duration_seconds: job.duration_seconds ?? undefined,
              orientation: job.orientation ?? this.jobs[idx].orientation,
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
      },
    });
  }

  removeJob(jobId: string) {
    this.activePolls.delete(jobId);
    this.jobs = this.jobs.filter((j) => j.job_id !== jobId);
  }

  // ── Lightbox ───────────────────────────────────────────────
  openExpandFromJob(job: JobEntry) {
    if (!job.presigned_url) return;
    this.downloadImageUrl = job.presigned_url;
    this.downloadJobId = job.job_id;
  }

  openExpandFromGallery(item: GalleryEntry) {
    if (!item.presigned_url) return;
    this.downloadImageUrl = item.presigned_url;
    this.downloadJobId = item.job_id;
  }

  openExpandFromSample(s: SampleEntry) {
    if (!s.presigned_url) return;
    this.expandedItem = {
      job_id: s.sample_id,
      presigned_url: s.presigned_url,
      template_key: '',
      style_key: '',
      isSample: true,
    };
  }

  closeExpand() {
    this.expandedItem = null;
  }

  // ── Order modal ────────────────────────────────────────────
  openOrderModal(job: JobEntry) {
    this.orderModalJob = job;
    this.orderError = '';
    this.orderSuccess = '';
    if (this.products.length === 0) {
      this.productsLoading = true;
      this.api.getProducts().subscribe({
        next: (resp: any) => {
          const list: any[] = resp?.products ?? resp?.data ?? (Array.isArray(resp) ? resp : []);
          this.products = list
            .map((p: any) => ({
              uid: p.productUid ?? p.uid ?? p.product_uid ?? '',
              label: p.title ?? p.name ?? this.uidLabel(p.productUid ?? p.uid ?? ''),
            }))
            .filter((p) => p.uid);
          this.productsLoading = false;
        },
        error: () => {
          this.productsLoading = false;
        },
      });
    }
  }

  openOrderFromGallery(item: GalleryEntry) {
    this.openOrderModal({
      job_id: item.job_id,
      template_key: item.template_key,
      style_key: item.style_key,
      status: 'completed',
      presigned_url: item.presigned_url ?? undefined,
      submitted_at: item.created_at ? new Date(item.created_at) : new Date(),
    });
  }

  closeOrderModal() {
    this.orderModalJob = null;
  }

  onOrderSubmitted(form: OrderForm) {
    if (!this.orderModalJob?.presigned_url) return;
    if (!form.product_uid) {
      this.orderError = 'Please select a product.';
      return;
    }
    this.orderSubmitting = true;
    this.orderError = '';
    this.orderSuccess = '';

    const payload = {
      image_url: this.orderModalJob.presigned_url,
      product_uid: form.product_uid,
      quantity: form.quantity,
      order_type: form.order_type,
      shipping_address: {
        firstName: form.firstName,
        lastName: form.lastName,
        addressLine1: form.addressLine1,
        addressLine2: form.addressLine2,
        city: form.city,
        postCode: form.postCode,
        country: form.country,
        email: form.email,
        phone: form.phone,
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

  private uidLabel(uid: string): string {
    const m = uid.match(/pf_([\d]+x[\d]+-mm)/);
    const size = m ? m[1].replace(/-mm$/, ' mm').replace('x', ' × ') : '';
    const pt = uid.match(/pt_([\w-]+)/);
    const paper = pt ? pt[1].replace(/-/g, ' ') : '';
    return [size, paper].filter(Boolean).join(' — ') || uid;
  }

  // ── Samples ────────────────────────────────────────────────
  loadSamples() {
    this.samplesLoading = true;
    this.api.getSamples().subscribe({
      next: (list) => {
        this.samples = list;
        this.samplesLoading = false;
      },
      error: () => {
        this.samplesLoading = false;
      },
    });
  }

  sampleDragOver = false;

  onSampleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.setSampleFile(input.files?.[0] ?? null);
  }

  onSampleDrop(event: DragEvent) {
    event.preventDefault();
    this.sampleDragOver = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) this.setSampleFile(file);
  }

  onSampleDragOver(event: DragEvent) {
    event.preventDefault();
    this.sampleDragOver = true;
  }

  onSampleDragLeave() {
    this.sampleDragOver = false;
  }

  setSampleFile(file: File | null) {
    this.sampleUploadFile = file;
    this.samplePreviewUrl = null;
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => (this.samplePreviewUrl = e.target?.result as string);
      reader.readAsDataURL(file);
    }
  }

  uploadSample() {
    if (!this.sampleUploadFile || this.sampleUploading) return;
    this.sampleUploading = true;
    this.sampleError = '';
    const form = new FormData();
    form.append('image', this.sampleUploadFile);
    this.api.uploadSample(form).subscribe({
      next: () => {
        this.sampleUploading = false;
        this.setSampleFile(null);
        this.loadSamples();
      },
      error: (err) => {
        this.sampleUploading = false;
        this.sampleError = err?.error?.error || 'Upload failed.';
      },
    });
  }

  deleteSample(sampleId: string) {
    this.api.deleteSample(sampleId).subscribe({
      next: () => {
        this.samples = this.samples.filter((s) => s.sample_id !== sampleId);
      },
      error: () => {},
    });
  }

  // ── Navigation ─────────────────────────────────────────────
  switchTab(tab: 'generate' | 'samples' | 'upload' | 'orders' | 'gallery' | 'order') {
    this.activeTab = tab;
    if (
      (tab === 'samples' || tab === 'upload') &&
      this.samples.length === 0 &&
      !this.samplesLoading
    ) {
      this.loadSamples();
    }
    if (tab === 'orders' && this.currentUser && !this.ordersLoading) {
      this.loadOrders();
    }
    if (tab === 'gallery' && this.currentUser && !this.galleryLoading) {
      this.loadGallery();
    }
  }

  regenerateFromJob(job: JobEntry) {
    this.api.regenerateGeneration(job.job_id).subscribe({
      next: (resp) => {
        this.jobs = this.jobs.filter(j => j.job_id !== job.job_id);
        this.jobs = [{ job_id: resp.job_id, template_key: job.template_key, style_key: job.style_key, status: 'pending', submitted_at: new Date(), orientation: job.orientation }, ...this.jobs];
        this.schedulePoll(resp.job_id);
      },
      error: (err) => { this.errorMsg = err?.error?.error || 'Regeneration failed.'; },
    });
  }

  regenerateFromGallery(entry: GalleryEntry) {
    if (!entry.source_url) {
      // Old generation — no source stored, fall back to manual flow
      this.selectTemplate(entry.template_key);
      this.switchTab('generate');
      this.errorMsg = 'Upload your pet photo to regenerate this portrait.';
      return;
    }

    this.api.regenerateGeneration(entry.job_id).subscribe({
      next: (resp) => {
        this.gallery = this.gallery.filter(g => g.job_id !== entry.job_id);
        this.jobs = [{ job_id: resp.job_id, template_key: entry.template_key, style_key: entry.style_key, status: 'pending', submitted_at: new Date(), orientation: entry.orientation }, ...this.jobs];
        this.schedulePoll(resp.job_id);
        this.switchTab('generate');
      },
      error: (err) => {
        this.errorMsg = err?.error?.error || 'Regeneration failed.';
      },
    });
  }

  downloadFromGallery(entry: GalleryEntry) {
    if (!entry.presigned_url) return;
    this.downloadImageUrl = entry.presigned_url;
    this.downloadJobId = entry.job_id;
  }

  deleteFromGallery(entry: GalleryEntry) {
    this.api.deleteGeneration(entry.job_id).subscribe({
      next: () => { this.gallery = this.gallery.filter(g => g.job_id !== entry.job_id); },
      error: () => {},
    });
  }

  goToMyGenerations() {
    this.switchTab('generate');
    setTimeout(() => {
      document.querySelector('.past-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  }

  goToGenerate() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    this.characterAnimation = 'happy';
    this.fabRotating = true;
    if (this.happyTimeout) clearTimeout(this.happyTimeout);
    this.happyTimeout = setTimeout(() => {
      this.characterAnimation = 'idle';
      this.happyTimeout = null;
    }, 2100);
    setTimeout(() => {
      this.fabRotating = false;
    }, 400);
    this.activeTab = this.activeTab === 'generate' ? 'samples' : 'generate';
  }

  onCharacterTap() {
    this.catMenuOpen = !this.catMenuOpen;
    if (this.catMenuOpen) {
      this.characterAnimation = 'happy';
      if (this.happyTimeout) clearTimeout(this.happyTimeout);
      this.happyTimeout = setTimeout(() => {
        this.characterAnimation = 'idle';
        this.happyTimeout = null;
      }, 1640);
    }
  }

  closeCatMenu() {
    this.catMenuOpen = false;
  }
}
