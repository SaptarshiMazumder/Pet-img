# Pet-to: Legal Payment Setup — Path 1 (Japan) vs Path 2 (India)

Research date: July 4, 2026. Not legal/tax advice — verify the gating items with a gyoseishoshi (Japan) and a CA (India).

---

## TL;DR

| | Path 1: You in Japan | Path 2: Mom in India |
|---|---|---|
| Gating item | 資格外活動許可 (individual permission) — discretionary, needs **employer consent** | She must genuinely own & run it (profits stay hers, she files taxes) |
| Payment stack | Stripe Japan (3.6%) — best-in-class | Dodo (MoR, ~4.5% intl) + Razorpay (domestic India) |
| Timeline | 1–3 months (permission is the wait) | 2–4 weeks to first international payment |
| Cost to start | ~¥0 (+optional gyoseishoshi ¥30–100k) | ~₹10–30k (current account balance, IEC, domain, CA) |
| Your name public? | Yes — 特商法 page must show your name/address | No — Dodo is seller of record; site shows "Nakama AI" brand |
| Main risk | Permission may be denied / employer says no | Razorpay intl approval uncertain; Dodo payout-hold complaints; must be genuinely her business |

**Key insight:** these paths can interact. Even under Path 2, if *you* do ongoing paid work for the business from Japan, you still need Japan-side permission and must declare that income in Japan. The clean Path 2 version is: it's her business and her profits; you contribute occasionally as unpaid family help, or as a formally engaged contractor (which triggers the Japan permission anyway).

---

## Path 1 — Run it yourself in Japan (Stripe)

### Why the permission is required
- 技人国 visa only covers work under contract with a Japanese org. Selling your own product = "operating a business" — prohibited without permission **even at ¥0 profit**. Subscriptions are inherently repetitive/continuous, so no "small-scale hobby" exemption applies.
- Routing money to an overseas account does NOT avoid this — the regulated act is running the business from Japan.

### Steps
1. **Employer consent** — check 就業規則, get written consent. This is a *statutory element* of the permission for work-visa holders, not just an HR courtesy. (days–weeks)
2. **Apply for 資格外活動許可 (個別/individual)** at your regional immigration bureau. Free. Attach: application form, residence card, passport, employer consent, and a self-drafted business plan (product, pricing, revenue estimate, hours/week, why it won't impede your main job, no office/no employees/no incorporation). Processing: **2 weeks–2 months.** Approval is discretionary — the "small-scale, subsidiary, employer consents" showing decides it. A gyoseishoshi (¥30–100k) meaningfully improves odds.
3. **After approval:** file 開業届 + 青色申告承認申請書 at tax office (same day, free; blue return = up to ¥650k deduction). Do NOT file 開業届 before the permission — it creates a paper trail of unauthorized business.
4. **Stripe Japan:** register as individual/sole proprietor (開業届 not required by Stripe). Residence card accepted, Japanese bank account for payouts. Site needs a **特定商取引法 page showing your name and contact info** — this is law, not Stripe policy. Verification 2–3 business days (up to 2 weeks). Fees: 3.6% domestic cards, +2% currency conversion; subscriptions via Payment Links/Checkout included.
5. **Taxes:** 確定申告 if side income >¥200k/yr (residence tax must be declared regardless of amount). Consumption tax exempt below ¥10M sales. Declared legal side income is neutral-to-positive at visa renewal; hidden income is what kills renewals and PR.

### Timeline & cost
1–3 months total; mandatory cost ≈ ¥0. The permission is the only uncertain step — everything after is routine.

### Notes
- Paddle: accepts Japan sellers but no JPY payouts (USD wire). Lemon Squeezy: Japan supported, 5%+$0.50; being folded into Stripe Managed Payments (2026 preview) — worth watching if you want a MoR to hide your personal details from checkout while staying legal.
- Stripe Atlas / US LLC: adds cost + US filings, solves nothing (you'd still owe Japanese tax and still need the visa permission). Skip.

---

## Path 2 — Mom's genuine business in India (Nakama AI)

### Legality core
- Sole proprietor = automatic beneficial owner under KYC/PMLA. A name-only arrangement where you fund/control it and take the economics is a prohibited **benami** arrangement. Genuine version: accounts, gateway, domain, contracts in her name; profits stay in her accounts and her tax return; she has real decision authority; you're a contractor or unpaid family help.
- Her lack of social media doesn't matter — no gateway checks that. What they check: PAN, Aadhaar, Udyam, bank, website policy pages.

### Steps
1. **Website** (week 0–1): product pages + terms, privacy, refund/cancellation, pricing, contact with Indian address. Required by every gateway; international activation is impossible without these.
2. **GST registration** (free, 3–7 days): technically disputed whether required below ₹20L for exporters, but register voluntarily — you need it to file an **LUT** (free, online) to export without charging 18% IGST. Note: once registered, her domestic Indian sales attract 18% GST from rupee one.
3. **IEC** (₹500, 1–2 days): not strictly mandatory for service exports, but some banks/platforms demand it. Get it.
4. **Current account** in firm name (week 1–3): savings account risks bank freezing on commercial activity. RBI KYC wants two firm-name documents — Udyam + GST works. Min balance ₹5–25k.
5. **Dodo Payments — international rail** (24–72h verification): true Merchant of Record; accepts Indian individuals with PAN + Udyam + even personal bank account; **their FAQ explicitly blesses the parent-owned-account pattern** (KYC, bank, ownership under parent's name; parent signs up with her email/phone). Checkout shows "Nakama AI" brand; Dodo is legal seller, handles global VAT/sales tax. Fees ~4% + $0.40 (+0.5% subscriptions); payouts bi-monthly, $50 min, as export remittance. **Caveat: young company, credible complaints of payout holds — don't let large balances accumulate.**
6. **Razorpay — domestic India rail**: proprietor KYC (PAN, Aadhaar, Udyam, bank) approved in 2–7 days for domestic (2% cards, 0% UPI, RBI-compliant subscriptions). International activation is a separate banking-partner approval — uncertain and slow for a zero-history merchant (weeks–months, may be declined initially). Use Dodo for international from day one; add Razorpay intl later once there's a track record.
7. **Her taxes:** business income at slab rates; likely eligible for presumptive 44AD (declare 6% of digital turnover, minimal books). CA ≈ ₹10–25k/yr. Keep FIRA/remittance docs per payout (FEMA proof); note SOFTEX→EDF regime change Oct 1, 2026 — CA should set up the workflow.
8. **You:** if paid as contractor — her firm files 15CA(/CB) per remittance, India–Japan DTAA applies, AND you need Japan-side 資格外活動許可 + declare it in Japan. If unpaid occasional family help — much less exposure, but the profits genuinely aren't yours.

### Timeline & cost
2–4 weeks to first international payment via Dodo; ~₹10–30k upfront.

### Rejected options
- **PayPal India:** export-only, no real recurring billing — backup button at best.
- **Stripe India:** still invite-only in 2026. **Paddle:** accepts Indian sellers, viable alternative to Dodo (~5% + $0.50, more established). **PayU:** intl needs paid add-on + possibly audited financials. **Lemon Squeezy:** India support unclear.

---

## Honest comparison

**Path 1 wins if** your employer consents and immigration approves: best fees (3.6% vs ~4.5–5%), Stripe's tooling, your name and social media front and center, income is yours, builds your record for PR. The catch: your name/address must appear on the site (特商法), and approval isn't guaranteed.

**Path 2 wins if** your employer refuses consent or you want revenue faster: live in 2–4 weeks, Dodo hides personal details behind the MoR, mom's identity never appears at checkout. The catch: the money is legally hers, not yours — that's not a workaround, it's the deal. If in substance you take the profits and control everything, it's benami + the Japan problems return.

**Pragmatic hybrid many people in your shoes use:** start Path 2 properly (fast revenue, genuinely her business, low stakes while validating the product) while pursuing Path 1's permission in parallel; if permission is granted, migrate the business to your own name in Japan with Stripe.

---

## Verify before acting
1. Gyoseishoshi consult (Japan): approval odds for your specific employer/contract situation. Many offer free first consultations.
2. CA consult (India): GST/LUT setup, EDF workflow post-Oct 2026, 44AD eligibility.
3. Employer 就業規則: side-business clause — this decides Path 1 before immigration does.

Full sources available on request — every claim above is backed by official (ISA, NTA, RBI, GST portal, Stripe, Razorpay, Dodo) or practitioner sources.
