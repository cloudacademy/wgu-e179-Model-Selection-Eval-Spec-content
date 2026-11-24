# Cardinal Trust Financial deployment brief

Cardinal Trust Financial is a retail and commercial bank. Consumer Payments is commissioning a real-time fraud flag for its private cloud within a hybrid cloud and on-premises estate. Transaction records must stay within the bank's approved jurisdiction. The service has standard CPU capacity and no dedicated GPU. At peak it must score at least 5,000 transactions per second with latency under 200 ms per transaction.

## A shift in the pilot

A payments analyst starts with the transaction record, its score and any recorded rationale. The desk reviews flagged payments and decides whether to escalate them. Its handover to the next shift must identify which priority cases still need acknowledgement. A customer query or an internal audit may arrive after the original analyst has left the shift.

Address your Task 1 summary to the payments security operations team. Model governance reviews the Task 2 evaluation. The procurement decision in Task 3 goes to an executive audience.

## Operating requirements and evidence


A positive label (1) denotes confirmed fraud. Label 0 denotes a legitimate payment. The operating point flags a record when its probability of class 1 is at least 0.50. The pilot portfolio sees about 20,000 payments on a typical day. The peak requirement covers the enterprise payments service. The payments desk reviews at most 240 flagged payments per day. An analyst must acknowledge a priority flag within 15 minutes. For a flagged transaction above $10,000, a human-reviewable, documented decision rationale must be available before escalation. Every flag must be logged with a retrievable rationale for internal audit and examination.

The bank has moderate risk tolerance. Missed fraud creates direct financial loss. Blocking legitimate payments affects customer trust and adds manual reviews. The bank's internal model policy requires an independent reader to be able to understand how the model operates, its assumptions and limitations, and the arrangements for ongoing performance monitoring. Its policy was adopted under historical SR 11-7 and the 2021 BSA/AML statement. The federal agencies replaced those issuances with revised, risk-based guidance in SR 26-2 on April 17, 2026. The rationale and review rules above are this bank's operating requirements.

Review flag rates by customer age bracket (Under 25, 25–61, 62+; reference 25–61) and customer gender (Male, Female, Nonbinary; reference Male). The internal screening band is 0.80–1.25 inclusive for the subgroup flag rate divided by its reference-group flag rate. The bank uses this screen to trigger review.

Source for the supervisory context: Board of Governors of the Federal Reserve System. (2026, April 17). *Revised guidance on model risk management* (SR 26-2). https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
