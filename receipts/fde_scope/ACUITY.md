# Acuity Real Estate (redacted)

Numbers: METRICS-SOT.md, last synced 2026-08-12.

## Customer problem

Inbound SMS leads needed qualification and CRM routing without dropping Spanish-language traffic.

## Constraints discovered

Bilingual EN/ES, sub-500ms response target on the production narrative, GoHighLevel as the system of record, broker-defined qualification rubric.

## First thin slice

Lead intake bot only: qualify, tag, write to GHL. Buyer and seller bots after the intake path was stable.

## Acceptance criteria

Warm leads reach the broker with CRM fields filled. No silent drop of Spanish threads.

## What was excluded

New marketplace CRMs. Model fine-tuning. Rebuilding GHL.

## Kill-check

If GHL writes failed or Spanish paths fell through, pause new bot types and fix intake.

## Result and handoff

Jan-Mar 2026 production run. 500+ inbound leads processed. 1,700+ tests at handoff. Audit of 226 existing GHL workflows. Zero production regressions (historical handoff claim).
