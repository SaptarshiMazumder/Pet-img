import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { LanguageService } from '../../services/language.service';
import { CreditPack } from '../../models';

@Component({
  selector: 'app-credits-modal',
  standalone: true,
  imports: [],
  template: `
    <div class="cm-backdrop" (click)="closed.emit()"></div>
    <div class="cm-panel" role="dialog" aria-modal="true">
      <button class="cm-close" (click)="closed.emit()" aria-label="Close">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>

      <h2 class="cm-title">{{ ja() ? 'クレジットを購入' : 'Buy credits' }}</h2>
      <p class="cm-sub">
        {{ ja()
          ? '1クレジットで、1枚のポートレートをHD・透かしなしでダウンロードできます。'
          : '1 credit unlocks the HD, watermark-free download of one portrait.' }}
      </p>

      <div class="cm-balance">
        {{ ja() ? '現在の残高' : 'Your balance' }}:
        <strong>{{ credits }} {{ ja() ? 'クレジット' : (credits === 1 ? 'credit' : 'credits') }}</strong>
      </div>

      @if (!paymentsEnabled) {
        <div class="cm-note">
          {{ ja()
            ? '決済は近日対応予定です。もうしばらくお待ちください。'
            : 'Payments are coming soon — please check back shortly.' }}
        </div>
      }

      <div class="cm-packs">
        @for (pack of packs; track pack.pack_id) {
          <div class="cm-pack">
            <div class="cm-pack-credits">{{ pack.credits }} {{ ja() ? 'クレジット' : 'credits' }}</div>
            <div class="cm-pack-price">\${{ pack.price_usd }}</div>
            <div class="cm-pack-unit">
              \${{ (pack.price_usd / pack.credits).toFixed(2) }} / {{ ja() ? '枚' : 'each' }}
            </div>
            <button
              class="cm-buy"
              [disabled]="!paymentsEnabled || buying !== null"
              (click)="buy(pack)"
            >
              @if (buying === pack.pack_id) {
                <span class="cm-spinner"></span>
              } @else {
                {{ ja() ? '購入' : 'Buy' }}
              }
            </button>
          </div>
        }
      </div>

      @if (error) {
        <div class="cm-error">{{ error }}</div>
      }

      <p class="cm-fineprint">
        {{ ja()
          ? '決済はDodo Payments（記録上の販売者）が安全に処理します。'
          : 'Payments are processed securely by Dodo Payments (Merchant of Record).' }}
      </p>
    </div>
  `,
  styles: [`
    .cm-backdrop {
      position: fixed; inset: 0; background: rgba(20, 16, 12, 0.55);
      backdrop-filter: blur(2px); z-index: 1000;
    }
    .cm-panel {
      position: fixed; z-index: 1001; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: min(92vw, 520px); max-height: 88vh; overflow-y: auto;
      background: #fdfbf7; border-radius: 16px; padding: 28px 24px;
      box-shadow: 0 24px 60px rgba(0,0,0,0.28);
      font-family: inherit; color: #2a241d;
    }
    .cm-close {
      position: absolute; top: 14px; right: 14px; border: none; background: transparent;
      color: #8a7f70; cursor: pointer; padding: 4px; border-radius: 8px;
    }
    .cm-close:hover { background: rgba(0,0,0,0.05); }
    .cm-title { font-size: 1.35rem; margin: 0 0 6px; }
    .cm-sub { color: #6b6154; font-size: 0.92rem; margin: 0 0 16px; line-height: 1.5; }
    .cm-balance {
      background: #f3ede2; border-radius: 10px; padding: 10px 14px;
      font-size: 0.95rem; margin-bottom: 16px;
    }
    .cm-note {
      background: #fff4e0; border: 1px solid #f0d9ac; color: #8a6314;
      border-radius: 10px; padding: 10px 14px; font-size: 0.88rem; margin-bottom: 16px;
    }
    .cm-packs { display: flex; flex-direction: column; gap: 12px; }
    .cm-pack {
      display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 12px;
      border: 1px solid #e6ddcd; border-radius: 12px; padding: 14px 16px;
    }
    .cm-pack-credits { font-weight: 600; font-size: 1.02rem; }
    .cm-pack-price { font-weight: 700; font-size: 1.1rem; }
    .cm-pack-unit { grid-column: 1; font-size: 0.8rem; color: #8a7f70; margin-top: -8px; }
    .cm-buy {
      grid-row: 1 / span 2; grid-column: 3;
      background: #b4552d; color: #fff; border: none; border-radius: 10px;
      padding: 10px 22px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
      min-width: 84px; display: inline-flex; align-items: center; justify-content: center;
    }
    .cm-buy:hover:not(:disabled) { background: #9c4423; }
    .cm-buy:disabled { opacity: 0.5; cursor: not-allowed; }
    .cm-spinner {
      width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.5);
      border-top-color: #fff; border-radius: 50%; animation: cm-spin 0.7s linear infinite;
    }
    @keyframes cm-spin { to { transform: rotate(360deg); } }
    .cm-error { color: #b4231d; font-size: 0.88rem; margin-top: 12px; }
    .cm-fineprint { color: #9a8f80; font-size: 0.78rem; margin: 16px 0 0; text-align: center; }
  `],
})
export class CreditsModalComponent {
  private readonly api = inject(ApiService);
  private readonly lang = inject(LanguageService);

  @Input() credits = 0;
  @Input() packs: CreditPack[] = [];
  @Input() paymentsEnabled = false;
  @Output() closed = new EventEmitter<void>();

  buying: string | null = null;
  error = '';

  ja(): boolean {
    return this.lang.lang() === 'ja';
  }

  buy(pack: CreditPack): void {
    if (!this.paymentsEnabled || this.buying) return;
    this.buying = pack.pack_id;
    this.error = '';
    const returnUrl = `${window.location.origin}/?checkout=success`;
    this.api.createCreditCheckout(pack.pack_id, returnUrl).subscribe({
      next: (resp) => {
        if (resp?.checkout_url) {
          window.location.href = resp.checkout_url;
        } else {
          this.buying = null;
          this.error = this.ja() ? 'チェックアウトを開始できませんでした。' : 'Could not start checkout.';
        }
      },
      error: (err) => {
        this.buying = null;
        this.error = err?.error?.error || (this.ja() ? 'エラーが発生しました。' : 'Something went wrong.');
      },
    });
  }
}
