# 3-Minute Emergency Script

Use when time is cut, the session overruns, or the live demo is unavailable. **Every claim is identical to
the 7-minute version** — this is a compression, not a different story.

Target ≈ 135 words/minute. Total ≈ 410 words.

---

## 0:00–0:25 · Problem *(slide 2)*

> "LMIS — problem statement 26246. Before a state sanctions training seats, it needs to know which
> district-and-trade combinations are heading for shortage. Today that's last year's targets plus a bit,
> because the evidence sits in six official sources that cannot be joined — five vintages spanning fourteen
> years, two occupation classifications, and **not one source carrying a district-by-occupation vacancy
> count**."

---

## 0:25–1:00 · Solution *(slide 4)*

> "We built the platform that fixes the fragmentation. Twenty-six official sources under a licence gate,
> into an immutable checksummed store, conformed onto NCO-2015, LGD geography and NIC sections through
> **official** concordances — and published so that every number carries its evidence status, confidence,
> coverage, vintage and source document.
>
> Forty tables, thirty API routes, four hundred and seventy-nine tests, and one command rebuilds everything
> from raw bytes."

---

## 1:00–1:40 · One demonstration *(live `#state/27`, or slide 7)*

> "Here's the product. Districts in Maharashtra, ranked on a relative demand allocation signal.
>
> Now read the caveat we print **above** the table: *within a state, this ordering equals the Udyam
> enterprise-share ordering.* We measured that — in **zero of thirty-six states** does it differ. So this is
> an enterprise-density ranking within a state, and we say so on the face of the product rather than calling
> it 'highest-demand districts'.
>
> And a district without Census coverage shows `NOT_AVAILABLE` **with the reason** — never a zero. No row in
> this system carries a signal of zero."

---

## 1:40–2:20 · Evidence discipline *(slides 8 → 9)*

> "Fifty-eight per cent of published NCS vacancies are PAN-India — attributable to no state. We never
> allocate them, so every district figure rests on the remaining forty-two per cent, and the page says so.
>
> And the gap the problem statement asks for: we don't publish one. Supply by state and trade is a joint
> distribution and we hold only its margins — twenty-one point eight per cent of the column margins, from a
> different scheme. Margins never determine an interior. We could produce a number; the error would be
> invisible and systematically wrong, and it informs real sanctioning money."

---

## 2:20–2:45 · Innovation + unlock *(slides 10 → 11)*

> "So the system distinguishes *'we don't have this data'* from *'this isn't identifiable'* — and enforces
> it in code. The app refuses to start if any output claims a shortage it can't measure. There's no
> machine-learning model in production, and I'd rather say that than invent one.
>
> One dataset changes it: **state-by-trade training outcomes with complete marginals**. With that, this
> platform computes the gap — no formula change."

---

## 2:45–3:00 · Close *(slide 12)*

> "We don't manufacture a skill gap from incomplete data. We build the evidence infrastructure that makes
> the gap computable when the right data arrives.
>
> I'd rather hand MSDE a specific data request than a number that restates an assumption. Happy to take
> questions."

---

## Compression rules

**Cut first, in order:** slide 3 (why it's difficult) · slide 5 (standardisation) · slide 6 (output table) ·
`/docs`.

**Never cut:** the Maharashtra caveat · the 58% residual · the identification argument · the closing ask.

**If you must go to 2 minutes:** problem (0:20) → one demo screen with its caveat (0:40) → the 58% and the
gap reason (0:40) → the one-dataset ask and the close (0:20).
