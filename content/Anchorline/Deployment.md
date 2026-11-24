# Anchorline Systems deployment brief

Anchorline Systems is a publicly traded US domestic issuer. Its Security Operations Center (SOC) operates a semi-autonomous triage service in its on-premises SIEM. The service must classify and prioritize an incoming alert within 2 seconds and process at least 10,000 alerts per hour at peak. It must use the current SOC compute allocation. External network egress for triage decisions is prohibited.

## A shift in the pilot

A SOC analyst receives an alert in the SIEM with a source, an event type and a severity score. The triage service assigns a priority. Before an escalation or containment action is finalized, the analyst reviews its rationale. At shift handover, the incoming analyst needs to see what was decided and which priority alerts still await acknowledgement.

Address your Task 1 summary to the SOC analysts and shift leads. Model governance reviews the Task 2 evaluation. The procurement decision in Task 3 goes to an executive audience.

## Operating requirements and evidence


A positive label (1) denotes a malicious alert. Label 0 denotes a benign alert. The model flags a record when its probability of class 1 is at least 0.50. A source system's severity score is a separate measurement; its existing escalation rule uses 0.75. The current pilot covers about 12,000 alerts on a typical day. The SOC can review 160 flagged alerts per day. Analysts must acknowledge priority alerts within 10 minutes. Any recommendation resulting in automated escalation, containment or system isolation needs a documented rationale for analyst review before finalization. All triage decisions must be logged with a retrievable rationale for internal audit and for any SEC materiality review.

The organization has moderate risk tolerance. Missing a malicious alert can leave an intrusion undetected in production. A false alert consumes analyst time and may isolate a system unnecessarily. Its enterprise contracts call for documented governance, detection and response processes under NIST CSF 2.0. SEC Form 8-K Item 1.05 generally requires disclosure within four business days of determining a cybersecurity incident is material. Annual Form 10-K disclosures cover cybersecurity risk management, strategy and governance.

Review flag rates by employee age bracket (Under 40, 40–59, 60+; reference Under 40) and employee gender (Male, Female, Nonbinary; reference Male). The SOC uses the inclusive screening band 0.80–1.25 for the subgroup flag rate divided by its reference-group flag rate.

Sources for the governance context: U.S. Securities and Exchange Commission. (2023, July 26). *Cybersecurity risk management, strategy, governance, and incident disclosure*. https://www.sec.gov/rules-regulations/2023/07/s7-09-22
National Institute of Standards and Technology. (2024). *The NIST Cybersecurity Framework (CSF) 2.0*. https://doi.org/10.6028/NIST.CSWP.29
