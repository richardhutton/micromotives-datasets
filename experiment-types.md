# Experiment types

Terms used throughout:

- **Factor:** one thing you change on purpose.
- **Level:** one of the options you try for it.
- **Factorial design:** every level of every factor crossed with every other.

Example: the reason given (none, rising costs, investing in the network) × the offer (none, a payment plan) = 6 versions.

---

## 1. A/B (Version test)

**Answers:** which version works better.

**How it works:** two or more versions of the same thing. Each person sees one, and everyone answers the same question.

**Commercial:** three pack designs, "free delivery" against "10% off", two email subject lines.

**Your data:** alcohol warning labels (21 labels), the DEL message tests.

**Notes:**
- The product calls this a "Message test". It's the most common type, and the builder includes "today" as the control unless you remove it. Pick one name.
- Pack designs need images. "Free delivery" against "10% off" works today.

---

## 2. Factorial (Mix test)

**Answers:** what each change does on its own, and whether they work better together.

**How it works:** two or more factors, each with a few levels, crossed into every combination. A 2 × 2 gives four versions, and each person sees one.

**Commercial:** a headline that leads on benefit or on price, shown with a product image or with people. A price shown monthly or yearly, with or without a discount badge.

**Your data:** calorie labels crossed with menu availability. Consent placement crossed with wording.

**Notes:**
- The product calls this a "Factor test" (`DESIGN_LABELS` in `spec.ts`). Pick one name.
- The builder can't show images yet. If this describes the product today, use a text example such as "with or without a customer quote".

---

## 3. Vignette (Story test)

**Answers:** whether details about a person or situation change how people judge it.

**How it works:** one short story with slots for the details that change, such as a name, age or job. Each slot has a few values, drawn at random for each story, so there are many versions. Each person reads a few and judges each one on its own.

**Commercial:** a late delivery, where the delay, the compensation and the apology vary, and people rate how satisfied they'd be. A supplier's profile, where years trading, certification and location vary, and people rate how far they'd trust it.

**Your data:** a job applicant, successful ageing, the stigma of flexible working.

**Notes:**
- Built as "Story test".
- The default is three stories per person. Say "usually three" if you want it exact.

---

## 4. Conjoint (Choice test)

**Answers:** which features make people choose one option over another, and what they'll trade for what. With price as a feature, it also shows what people will pay.

**How it works:** each option is described by the same features, such as price, contract length or exit fee. Each feature's value is drawn at random, so every round shows a new pair. People pick one, or "neither", over several rounds.

**Commercial:** energy tariffs, broadband plans, software tiers, contract terms between businesses.

**Your data:** Brexit deals, voting online, taking in a lodger.

**Notes:**
- Built as "Choice test", in pairs only ("Charity A" and "Charity B"). Rounds default to 3.
- "Neither" is added only when the user asks for it.
- What people will pay needs a results view that isn't built yet. It also needs several price points.
- How to read the results: see `conjoint-example.md`.

---

## 5. Within-subject (Line-up test)

**Answers:** how several versions compare when each person sees all of them.

**How it works:** each person sees several versions, one at a time in random order, and answers the same question about each.

**Commercial:** four ad concepts, five flavour ideas.

**Your data:** food photos, political ads (four each).

**Notes:**
- "Using fewer people" was dropped. Simulated people cost nothing to recruit. The real reason to use this test is that people who see every version compare them, so their answers become relative. Use it when the real decision is a comparison, like products on a shelf.
- In the product this isn't its own type. It's a message test with "each person sees" set to all, and the card shows the pill "Everyone sees all".
- Food photos need images, which aren't built yet.

---

## 6. Paired comparison (Head-to-head)

**Answers:** which items in a long list are strongest, ranked from best to worst.

**How it works:** pairs are drawn at random from the list. People pick the better one, over several rounds. Each item's score is how often it wins.

**Commercial:** thirty candidate product names, a list of taglines.

**Your data:** political arguments, statements about aid, pairs of photos.

**Notes:**
- Not built. The prompt lists rankings as "coming later".
- Don't confuse it with the choice test. A choice test builds options from features to find which feature matters. Here the items are fixed, and you want to know which item wins.
- A model such as Bradley-Terry refines the win rate when items meet different opponents.

---

## 7. MaxDiff (Priority test)

**Answers:** which items in a long list matter most, and by how much.

**How it works:** each screen shows four or five items from a list of ten to thirty. People pick the best and the worst. Sets repeat until every item has appeared several times. Each item scores how often it was picked best, minus how often it was picked worst.

**Commercial:** twenty features to prioritise, fifteen claims to find which is most believed.

**Your data:** none yet.

**Worked example** (numbers made up to show the sum). Score = (best − worst) ÷ times shown.

| Item | Shown | Best | Worst | Score |
|---|---|---|---|---|
| Free returns | 10 | 6 | 0 | +0.6 |
| Next-day delivery | 10 | 3 | 1 | +0.2 |
| Loyalty points | 10 | 1 | 4 | −0.3 |
| Gift wrapping | 10 | 0 | 5 | −0.5 |

Scores run from −1 (always worst) to +1 (always best). The gaps show how far apart items are, which a plain ranking can't.

**Notes:**
- One screen tells you a lot. Best A and worst D out of A, B, C and D settles five of the six pairs.
- Research firms often fit a logit model, sometimes hierarchical Bayes. It usually ranks items the same way as the simple count.
- Not built. With no training data for it, it would be Beta.

---

## 8. Choice set (Shelf test)

**Answers:** what people pick when they face many options at once, as they would in a shop, and how a change shifts that.

**How it works:** people see a shelf, menu or page of options and choose one, or none. Each version changes one thing about it, such as a label, the order or what's on offer.

**Commercial:** a new pack on a shelf, a menu redesign, an app store listing.

**Your data:** vending machines, menus, portion sizes. Online supermarkets follow once images are in.

**Notes:**
- Text menus with a changed label work today, as a message test with a pick-one measure and "None of these".
- Changing what's on offer doesn't fit yet. The measure's options are the same in every version, so people could pick items they never saw.
- A visual shelf needs images.

---

## 9. Order and priming (Context test)

**Answers:** whether what people see or hear first changes their answer.

**How it works:** everyone gets the same material, but in a different order or after something different beforehand. Each person sees one version.

**Commercial:** whether showing the price before the features changes interest, and whether asking about satisfaction first changes how likely people are to recommend.

**Your data:** the Innovation Panel order tests.

**Notes:**
- Something shown first works today, as a message test. The builder's opening has "What people hear beforehand" for it.
- The order of the material works today, as a message test with one version per order.
- The order of the questions doesn't. Measures are asked in a fixed order in every version.

---

## 10. List experiment (Sensitive count)

**Answers:** how common something is when people won't admit to it directly.

**How it works:** people see a short list and say only how many items apply to them, never which ones. Half see the list with one extra item, the sensitive one. The difference between the two halves' average counts is the share of people it applies to.

**Commercial:** sharing an account, returning worn clothes, buying fakes, ignoring rules at work.

**Your data:** attitudes to immigration, sexual identity.

**Worked example.** Group 1 sees four everyday items:

1. I've bought something online this month
2. I've been to the cinema this year
3. I own a bike
4. I've cooked a meal from scratch this week

Group 2 sees the same four, plus:

5. I've returned clothes after wearing them

Group 1 averages 2.0 and Group 2 averages 2.3. Both groups answer the first four the same way on average, so the extra 0.3 comes from item 5. About 30% have returned worn clothes, and no one ever said so.

**Notes:**
- It works today as a message test. The two versions are the list without item 5 (the control) and the list with it. The measure is a number from 0 to 5.
- Why it suits simulation: the model learns from real people, including what they won't admit. Asked directly, it would probably repeat their under-reporting. Asked through the list, it shows the honest rate.

---

## 11. Single condition (Baseline)

**Answers:** where people stand now, with nothing compared.

**How it works:** everyone sees the same thing and answers the same question.

**Commercial:** how a brand is seen today, and how likely people are to buy before a launch.

**Your data:** three experiments.

**Notes:**
- Built as "Single question".
- When the what-if is really "would this change minds?", the builder suggests a control or a second version.
- To track how things change, run it again later.
- It's the rarest type in the training data, which is expected for randomised experiments.

---

## Two things that cut across types

### Price isn't its own type

It's a feature in a choice test, or the versions in a version test. In a version test each person sees one price. The share who would buy at each price gives the demand curve.

Example (made up to show the sum):

| Price | Would buy | Revenue per 100 people |
|---|---|---|
| £8 | 70% | £560 |
| £10 | 55% | £550 |
| £12 | 35% | £420 |

£8 and £10 earn about the same, and £12 loses money.

### Reach (TURF) isn't its own type either

It's a way of reading priority test or shelf test answers: which small set of options together reaches the most people.

Example (made up): flavour A appeals to 40% and flavour B to 35%, but they're mostly the same people. Flavour C appeals to only 25%, mostly people A misses. A and C together might reach 60%, while A and B reach 45%. The best range is the two that cover each other's gaps, not the two most popular.

TURF needs a results view that isn't built yet.

