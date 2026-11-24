# Cardinal Trust Financial model and data record
The supplied artifact is a trained scikit-learn pipeline. It accepts a DataFrame of records. The `prepare` step passes the following numeric fields through unchanged: amount, velocity, geolocation_distance. It one-hot encodes merchant_category, customer_age_bracket, customer_gender and ignores previously unseen categories. The `classifier` step is a gradient-boosted tree classifier. The settings used are in `evaluation/model_settings.json`. The identifier and UTC timestamp provide record context. They do not enter the classifier.

The assigned explanation IDs are **C-EV-00010** and **C-EV-00231**. One prediction is correct and one is incorrect. Match these identifiers to the label column in the held-out evaluation file when checking the two cases. Report class-1 probability as the confidence score for both sides of every pair.

| File | Contents |
| --- | --- |
| training_sample.csv | Separate labeled training sample for fresh validation copies and explanation background |
| evaluation_dataset.csv | Fixed held-out records and ground truth labels |
| paired_records.csv | Three rows; all record fields end in `_original` or `_modified` |
| drift_reference.csv | Earlier baseline period without outcome labels |
| drift_current.csv | Later production period without outcome labels |
| model.pkl | Trained pipeline |
| model_settings.json | Configuration and field names |

The three pairs concern an overnight electronics payment, a midday pharmacy payment outside the usual area and an evening local grocery payment.

All times are UTC. Counts are nonnegative integers. Amount is in US dollars. Velocity is the number of payments by the same account in the preceding 10 minutes. Geolocation distance is in miles from home. Merchant category describes the business. Age bracket and gender are the audit groups defined in the deployment brief. The identifier is unique within each independent dataset. Dates and identifiers establish the observation window and are excluded from the drift feature matrix. All records are synthetic.

## Observation windows

The labeled training sample covers January 1–28, 2025. The held-out evaluation covers June 1–28. For the drift comparison, the reference window is March 1–28 and the current window is July 1–28. These are simulated observation periods. The two drift files contain no outcome labels.
