# UKDS permission granted: Innovation Panel (SN 6849), EUL clause 5.5

Written permission from the UK Data Service, received by rich in October 2026. The
emails below are copied word-for-word from what rich pasted into the session.

## 1. Request (sent by rich, Mon 12 Oct 2026)

> Dear UK Data Service,
>
> I am a registered user of SN 6849 (Understanding Society: Innovation Panel). I am training a language model to predict how people respond in survey experiments, using the Innovation Panel.
>
> Under clause 5.5 I would like written permission to:
>
> 1. Store the derived data (demographic attributes, the question and condition text, and each answer, with identifiers hashed) in a private Hugging Face repository that only I can access.
>
> 2. Train the model on a dedicated cloud GPU server rented in my name and accessible only to me, deleting the data from it after each training run.
>
> The data and the trained model would not be published or shared.
>
> I would also like to use an AI coding assistant on the questionnaire text and summary counts, not on respondent-level data. Please let me know if that requires permission too.
>
> Kind regards,
> Rich Hutton

## 2. UKDS question (Will Taylor, IT Security Manager)

> Could you tell me a bit more about your cloud GPU server please, in particular what platform it is on, and how it is configured to control access?

## 3. rich's reply

> The GPU is for fine-tuning an open-weight language model (Qwen) with supervised fine-tuning, training it on the Innovation Panel data so it learns to predict how people answer the survey experiments. The base model is publicly available, but the fine-tuned version I train will stay private.
>
> The GPU server would be on RunPod (runpod.io), using their Secure Cloud tier in one of their EU data centres. RunPod hold ISO 27001:2022 (certificate RUN-ISMS-20260827, valid to Aug 2029) and have SOC 2 Type II and SOC 3 reports, and Secure Cloud runs in Tier 3/4 data centres. Their compliance page is here: https://www.runpod.io/legal/compliance
>
> I should have been clearer in my first email when I said "dedicated". It's a pod, which is a container with its own GPU running on a shared host. RunPod keep each pod isolated from other customers, and their terms don't allow hosts to look at pod data.
>
> On access:
>
> - the RunPod account is mine only, with MFA on
> - I connect to the pod over SSH with my own key only, no password login and no other ports open
> - the data is pulled onto the pod from my private Hugging Face repo using a read-only token that only I have
> - the data only sits on the pod's own disk (no persistent storage), and I terminate the pod after each training run, which wipes it
> - the trained model stays private and won't be published or shared

## 4. Grant (Will Taylor, UKDS)

> Thanks for the detailed explanation. We've discussed this internally, and we confirm permission granted for the entirety of your request.

## What this allows

| | Allowed? |
|---|---|
| Derived IP rows in rich's **private** Hugging Face repo | yes |
| Training on a **RunPod Secure Cloud pod** (EU, MFA, SSH key, no persistent volume, terminated after each run) | yes |
| AI coding assistant (Claude) on **questionnaire text and summary counts** | yes |
| AI coding assistant on **respondent-level values** (persona or response values, rows) | **no**: not requested |
| Jev, Voyage, public repos, other clouds | no: not requested |
| Publishing or sharing the fine-tuned model | no |
