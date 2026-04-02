import { Component, EventEmitter, Input, OnChanges, Output, inject } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { LanguageService } from '../../services/language.service';
import { RegionService } from '../../services/region.service';

export interface PricingInfo {
  country: string;
  amount: number;
  currency: string;
  symbol: string;
  label: string;
}

@Component({
  selector: 'app-download-modal',
  standalone: true,
  imports: [],
  templateUrl: './download-modal.component.html',
  styleUrl: './download-modal.component.css',
})
export class DownloadModalComponent implements OnChanges {
  private api = inject(ApiService);
  private region = inject(RegionService);
  readonly lang = inject(LanguageService);

  @Input() imageUrl: string | null = null;
  /** Set when the preview is a user-owned generation (not a sample). */
  @Input() downloadJobId: string | null = null;
  @Input() loggedIn = false;
  @Input() creditBalance: number | null = null;
  /** Must match backend DOWNLOAD_CREDIT_COST (default 10). */
  @Input() downloadCreditCost = 10;

  @Output() closed = new EventEmitter<void>();
  @Output() payClicked = new EventEmitter<PricingInfo>();
  @Output() creditsUpdated = new EventEmitter<number>();

  pricing: PricingInfo | null = null;
  loadingPrice = true;
  consumingCredit = false;
  creditConsumeError: string | null = null;

  get canUseCredit(): boolean {
    const cost = this.downloadCreditCost > 0 ? this.downloadCreditCost : 10;
    return !!(
      this.loggedIn &&
      this.downloadJobId &&
      this.creditBalance !== null &&
      this.creditBalance >= cost
    );
  }

  get useCreditsButtonLabel(): string {
    const n = this.downloadCreditCost > 0 ? this.downloadCreditCost : 10;
    return this.lang
      .t()
      .credits.useCreditsForDownload.replace(/\{\{count\}\}/g, String(n));
  }

  ngOnChanges() {
    if (!this.imageUrl) {
      this.pricing = null;
      this.loadingPrice = false;
      this.creditConsumeError = null;
      return;
    }
    this.creditConsumeError = null;
    this.loadingPrice = true;
    this.pricing = null;
    this.api.getPricing().subscribe({
      next: (p) => {
        this.pricing = p;
        this.loadingPrice = false;
      },
      error: () => {
        this.pricing = null;
        this.loadingPrice = false;
      },
    });
  }

  /** Matches backend defaults when /pricing is unavailable */
  fallbackPricing(): PricingInfo {
    const cc = this.region.countryCode;
    if (cc === 'JP') {
      return { country: 'JP', amount: 2000, currency: 'JPY', symbol: '¥', label: '¥2,000' };
    }
    if (cc === 'IN') {
      return { country: 'IN', amount: 1100, currency: 'INR', symbol: '₹', label: '₹1,100' };
    }
    return { country: 'US', amount: 13, currency: 'USD', symbol: '$', label: '$13' };
  }

  /** Single object for the pay button when the API fails */
  get payFallback(): PricingInfo {
    return this.fallbackPricing();
  }

  consumeCreditForDownload() {
    const jobId = this.downloadJobId;
    if (!jobId || !this.canUseCredit || this.consumingCredit) return;
    this.consumingCredit = true;
    this.creditConsumeError = null;
    this.api.downloadWithCredit(jobId).subscribe({
      next: (r) => {
        this.consumingCredit = false;
        this.creditsUpdated.emit(r.credits_remaining);
        void this.downloadPreview();
      },
      error: (err: any) => {
        this.consumingCredit = false;
        const cost = this.downloadCreditCost > 0 ? this.downloadCreditCost : 10;
        if (err?.status === 402) {
          const n = err?.error?.required_credits ?? cost;
          this.creditConsumeError = this.lang
            .t()
            .credits.insufficientCreditsForDownload.replace(/\{\{count\}\}/g, String(n));
        } else {
          this.creditConsumeError = this.lang.t().credits.creditDownloadFailed;
        }
      },
    });
  }

  /** Called only after credits are deducted or payment succeeds — not a free save. */
  async downloadPreview() {
    const url = this.imageUrl;
    if (!url) return;
    try {
      const res = await fetch(url, { mode: 'cors' });
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      const ext = blob.type.includes('png') ? 'png' : blob.type.includes('webp') ? 'webp' : 'jpg';
      a.download = `pet-portrait.${ext}`;
      a.click();
      URL.revokeObjectURL(objectUrl);
    } catch {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }
}
