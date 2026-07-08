# HANDOFF: Pet-to.com × Dodo Payments Setup (Nakama AI / India)

> Created 2026-07-04 in a Cowork session. Purpose: continue this work in a new chat with zero context loss.
> Companion file: `pet-to-payments-research.md` (same folder) — recovered from a crashed earlier session; contains the Japan (Path 1) vs India (Path 2) legal analysis. **Path 2 (India) was chosen.**

---

## 1. Situation

- **Website/product**: https://pet-to.com — "Pet Generator": AI transforms pet photos into Edo-era / oil-painting style portraits. Code lives in this folder (`Pet-img`): Flask backend, Angular frontend (`frontend-ng`), GCP Cloud Run (dev/staging/prod via Terraform), image gen on RunPod/ComfyUI, prints fulfilled via **Gelato** print-on-demand.
- **Merchant**: user's **mother** in India. Sole proprietor, enterprise name **"Nakama AI"** (Udyam-registered). Has **PAN, NO GST**, only a **savings account**. No social media. Taxes filed in India.
- **User**: son, based in Japan (work visa — see companion file for why he can't easily run it himself; Path 2 = it must genuinely be HER business, profits hers, or it's benami).
- **Emails**: domain **nakamaai.co** with support/contact email (`contact@nakamaai.co` already used in order-confirmation emails in code) + a nakamaai Gmail.
- **Goal**: accept payments domestically (India) + internationally (USA/UK/Japan/EU) via **Dodo Payments** (MoR), minimum friction, ASAP.

## 2. Key decisions made

1. **Dodo = digital products only.** Physical framed prints will NOT go through Dodo (prohibited category — see §5).
2. **Prints hidden from the site during Dodo review**; later sold via a separate rail (NOT Razorpay — user says he **cannot use Razorpay**). Chosen alternatives: **Cashfree primary + PayPal India business for international manual orders** (see §7).
3. **Sign-up email**: use her **@nakamaai.co** address (professional, matches enterprise); Gmail as recovery. Caveat: keep domain renewed; user/mum must have OTP access.
4. Manual fulfillment workaround for prints ("customer pays Dodo, I order prints myself") was **rejected** — Dodo's ban is on what the buyer receives, not fulfillment logistics; chargebacks for physical items would expose it (enforcement: holds, suspension, fines up to $425k).
5. Pending user confirmation at handoff time: **digital pricing** (suggested ¥500–1,000 / $4–8 per HD generation, possibly credit packs + 1 free low-res preview) and **customer-acquisition answer** for the form. Claude offered to implement code changes (hide prints, add paid digital flow with Dodo checkout) — not yet started.

## 3. Critical code finding

- **Digital generation is currently FREE** — the only prices in the code are framed prints (`backend/config/prices.py`: FRAME_CATALOG ¥4,300–27,600; regions IN/JP with shipping; JPY→INR/USD conversion; `backend/routes/print_orders.py` → Gelato). README: dev env = ¥1 test pricing, staging/prod = real prices.
- Therefore: once prints are hidden, **the site has nothing for sale** → Dodo rejects sites where nothing can be purchased. A paid digital product MUST be added before applying.

## 4. Dodo onboarding — verified facts (docs.dodopayments.com, July 2026)

- **She onboards as "Individual", NOT Organization** — classification follows the *bank account type*, not certificates (FAQ Q36). Udyam holder + personal account = Individual. Picking "Organization" wrongly = application On-Hold.
- **Docs needed**: PAN (mandatory for Indian individuals), government photo ID (physical Aadhaar/passport/DL — no photocopies) + live selfie via **Persona**. Udyam NOT required/used. GST optional below threshold.
- **Savings/personal account is fine** ("You don't need a business bank account"). HARD RULE: account name must exactly match her KYC ID. **Do NOT use an account titled "Nakama AI"** — mismatch = rejection.
- **Parent-account pattern explicitly allowed** (FAQ Q25): she signs up with HER email + mobile; all KYC, bank, ownership in her name; she must personally do the selfie.
- **3 forms in order**: Product Information Form → Persona KYC → Bank Verification.
- **Social media**: form has a "Social media presence" field ("links to your product or founder social media profiles") — nothing says it's mandatory. **A live website IS effectively mandatory** (FAQ Q5; LinkedIn can't substitute; no-website cases → support@dodopayments.com). Plan: create an Instagram for pet-to.com (visual product, perfect fit) and/or founder LinkedIn.
- **Website requirements**: live + complete (no "coming soon"/waitlist/placeholder — policy-level auto-reject), visible pricing, product usable immediately after purchase, everything matching the form ("website mismatch" = documented rejection/enforcement reason). Privacy/Refund/Terms pages not explicitly required, but expected — Dodo has a free generator: https://dodopayments.com/tools/policy-generator
- **Timeline**: 24–72 working hours typical (excl. weekends/Indian holidays). Test-mode integration allowed before approval (test.dodopayments.com). Live payments + payouts unlock after approval + monitoring review. One appeal allowed on rejection.
- **Category flag**: "AI content generation" is restricted-but-reviewable → enhanced due diligence, slower review. Declare honestly; misclassification is enforceable.

## 5. Why prints can't touch Dodo

- Merchant Acceptance Policy prohibits **physical goods** and in-person services "even if booking or payment happens online". Dodo is legal seller of record — if money flows through Dodo checkout and a framed print ships, Dodo sold a physical good regardless of who fulfills.
- Detection: site re-review at activation/first transaction/before first payout; "item not received" chargebacks.
- Also prohibited (relevant if product evolves): marketplaces/forwarding funds, bookings of in-person services, manual digital services. If pet-to ever books groomers/walkers etc. → rejected.
- **Rule of thumb: not one rupee for a physical item may pass through Dodo checkout.** After approval, prints can resurface on the site paid via a clearly separate non-Dodo rail; honest answer if asked: "prints sold separately via Cashfree/PayPal; Dodo handles only digital."

## 6. Dodo commercials (verified)

- MoR selling to 226 countries incl. India, US, UK, JP, EU. Dodo handles buyer-country VAT/GST/sales tax, chargebacks ($30 passthrough), refunds ($1), invoicing, fraud.
- Fees: **4% + $0.40** base; +1.5% international; +0.5% subscriptions; India-domestic 4% + $0.15 (stacking with intl fee ambiguous). PayPal wallet currently paused. Refund $1; dispute $30.
- **Payouts: USD/EUR/GBP only (INR payouts discontinued)**, bi-monthly (1–15 paid ~18th; 16–EOM paid ~4th), $50 minimum, $5 fee if payout < $1,000, SWIFT USD $25 for non-US; bank converts to INR.
- India-buyer quirks: RBI 48h pre-debit notification delay on subscription renewals (Indian cards/UPI); e-mandate default limit ₹15,000; UPI needs billing country IN + INR.

## 7. Prints payment stack (Razorpay EXCLUDED by user)

- **Primary: Cashfree** — paperless sole-prop onboarding (PAN + Aadhaar + bank proof; **Udyam explicitly accepted**); physical goods OK; domestic 1.6% promo (signup before 31 Jul 2026, needs UPI ≥40% volume) / 1.95%; **international cards on same account** (toggle/per-merchant approval, not guaranteed for new merchants) 2.69–2.99%, 140+ currencies incl. JPY, INR settlement, monthly FIRC; first PA-CB (E&I) licence holder. Gotcha: fund-hold complaints; current account safer than savings.
- **International stopgap: PayPal India business** — self-serve (her PAN + bank, name must match), invoice/payment links with NO site integration (fits manual print-order workflow), physical goods OK (tracked shipping for Seller Protection), auto-convert + auto-withdraw to Indian bank ~24h, free weekly digital FIRA, purpose code P0101/P0104 (goods). ~8% effective cost (4.4% + fixed + 3–4% FX + GST on fees). No domestic INR.
- **Domestic backup: PhonePe PG** (currently 0% standard plan, easy proprietor KYC). **Large custom orders: Wise Business payment request** (receive-only for Indian businesses; e-FIRA ~$2; personal Wise accounts can't receive in India from 5 Apr 2026) or SWIFT invoice.
- Skip: Stripe India (invite-only), Instamojo (5%+₹3, no PA licence), CCAvenue (9-doc paperwork), 2Checkout (FX wire, no FIRA), Airwallex (SG entity, B2B), Paytm PG (viable since Nov 2025 licence but stricter individual KYC), UPI from foreign buyers (not possible).
- Physical-export caveats: courier customs (CSB-IV/V) + GST registration practically mandatory for exporting *goods* — BUT if prints are fulfilled by a print seller in the buyer's country (Gelato-style, nothing ships from India), the goods-export characterization may not apply → **CA question**.

## 8. India tax/compliance summary

- **GST**: below ₹20L aggregate turnover, pure export of services → **no GST registration required** (Notification 10/2017-IT; mainstream view, minor contrary view exists). Above ₹20L: register + **LUT every April** (zero-rated exports). Recovered research (companion file) suggests registering voluntarily anyway; note: once registered, domestic Indian sales attract 18% GST from rupee one.
- **"Sale to MoR = export" position**: supported by Dodo's reseller MSA (Delaware-law, Dodo Payments Inc.; also UK entity Dodope Payments Ltd + **Indian entity Sarvapanchhi Technologies Pvt Ltd**); strengthened by 30-Mar-2026 omission of Sec 13(8)(b) IGST (intermediary PoS now recipient location). Not settled law — keep MSA, invoices to Dodo, payout ledgers, FIRA per payout as defense file.
- **⚠ Biggest open question — ask Dodo in writing (support@dodopayments.com):**
  1. Which legal entity is counterparty/payer for her payouts, especially for Indian-customer (UPI/INR) sales — Delaware Inc. or the Indian affiliate? (If Indian affiliate pays in INR domestically → no inward remittance, no FIRA → undermines export/zero-rating for those sales.)
  2. Do payouts arrive as foreign inward remittance with **FIRA** (what purpose code — likely P0802) or domestic credits? FIRA issuance is NOT documented publicly.
  - Practical test: run one small payout and check with her bank how it lands.
- **Income tax**: her business income, slab rates (ITR-3/4). Presumptive: 44AD (6% of digital receipts) arguable for SaaS *product*; 44ADA (50%) if characterized as profession. CA to confirm.
- **FEMA**: savings account tolerated at small scale, but recurring P0802 credits typically make banks demand a current account (Udyam + one more doc opens one). From **1 Oct 2026**: SOFTEX replaced by monthly consolidated **EDF filing via AD bank** for ALL service exports (FEMA 23(R)/2026); build into routine. EDPMS entries ≤₹10L self-closable.
- **Benami warning** (from companion file): must genuinely be her business — her accounts, her profits, her tax return, real decision authority; user contributes as unpaid family help or formal contractor (contractor pay to Japan triggers 15CA/CB + Japan-side permission).

## 9. Draft Product Information Form answers (ready to adapt)

- Website: https://pet-to.com
- Description: "An AI tool that transforms photos of pets into Edo-era Japanese and classical oil-painting style portraits, delivered as instant high-resolution digital downloads."
- Category: AI content generation / digital goods (honest → enhanced review)
- Delivery: instant digital download from the website after purchase
- Automation: fully automated, self-serve, no manual work per order
- Compliance-sensitive: AI-generated imagery from customer pet photos; no human likeness, no restricted content
- Integration: hosted checkout / API on own website
- Stage: live and functional
- Customer acquisition: **PENDING user answer**
- Social media: **PENDING** — plan: create pet-to.com Instagram (+ optionally founder LinkedIn for mum)

## 10. Action checklist (state at handoff)

**Site (before applying):**
- [ ] Hide/disable print & framing flow (order-flow component, print-order-modal, shipping, `/print/order` route)
- [ ] Add paid digital product with visible pricing (amount TBD by user; suggestion ¥500–1,000 / $4–8 per HD generation; free low-res preview as hook)
- [ ] Integrate Dodo checkout (test mode first: test.dodopayments.com)
- [ ] Add Privacy Policy, Refund Policy, Terms (Dodo policy generator), Contact page (contact@nakamaai.co)
- [ ] Remove any dead buttons / placeholder content; site content must match form answers

**Mum / accounts:**
- [ ] Create pet-to.com Instagram (or similar) for the social field
- [ ] Dodo sign-up with her @nakamaai.co email + her mobile → account type **Individual**
- [ ] She does Persona KYC (physical ID + selfie; camera permissions = top pain point)
- [ ] Bank verification: her personal savings account, name matching ID exactly
- [ ] Email Dodo support the two §8 questions (entity + FIRA) in writing
- [ ] Cashfree onboarding for prints rail (later, after Dodo approval); PayPal India business account for international manual print orders
- [ ] CA consult: GST/LUT decision, 44AD vs 44ADA, EDF workflow post-Oct-2026, cross-border print fulfillment characterization
- [ ] After approval: one small live sale → verify how payout lands at the bank (FIRA? purpose code?)

**Division of labor note (assistant constraints):** the AI assistant can draft all form answers and (with Chrome extension + user confirmation) fill non-sensitive form fields, and can edit the codebase; it can NOT create the account/password, do KYC, or enter bank/ID numbers — she does those (~10 min).

## 11. Sources (primary)

- Dodo verification: https://docs.dodopayments.com/miscellaneous/verification-process
- Dodo FAQ (Q5, Q25, Q35, Q36, Q40, Q44, Q104): https://docs.dodopayments.com/miscellaneous/faq
- Merchant Acceptance Policy: https://docs.dodopayments.com/miscellaneous/merchant-acceptance
- Review & Monitoring Policy: https://docs.dodopayments.com/miscellaneous/review-monitoring-policy
- Pricing: https://dodopayments.com/pricing · Payouts: https://docs.dodopayments.com/features/payouts/payout-structure
- India payment methods: https://docs.dodopayments.com/features/payment-methods/india
- Dodo MSA/terms (reseller model, entities): https://dodopayments.com/legal/terms-of-use
- Dodo blogs: /blogs/get-paid-usd-developer-india · /blogs/accept-payments-without-company · /tools/policy-generator
- FIRA/FIRC gap: https://niryatbox.com/blog/dodo-payments-fira-firc-india-saas-exporters · https://www.skydo.com/blog/dodo-payments-features-and-fees
- GST/export: Notification 10/2017-IT analyses (taxguru/cleartax); intermediary change 30-Mar-2026 (taxguru/caclubindia); SOFTEX→EDF: winvesta/majmudarindia/EY
- Cashfree: https://www.cashfree.com/payment-gateway-charges/ · /accept-international-payments/ · /docs/help/account/account-activation
- PayPal India: https://www.paypal.com/in/webapps/mpp/merchant-fees · /in/business/firc-certificate · purpose codes help
- PhonePe PG pricing: https://www.phonepe.com/business-solutions/payment-gateway/pricing/
- Stripe India invite-only: https://support.stripe.com/questions/stripe-accounts-are-invite-only-in-india
- Wise India receiving: https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/receiving-payments-for-indian-businesses

*Not legal/tax advice — GST-via-MoR position and print-fulfillment characterization need a one-time CA review once revenue is real.*
