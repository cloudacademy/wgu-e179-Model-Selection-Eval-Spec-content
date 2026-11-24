# Method syntax
The identifiers below are placeholders. Each expression shows the interface to one method. The guide contains no worked case.

~~~python
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, KFold, cross_val_score
splitter = splitter_class(n_splits=k, shuffle=True, random_state=seed)  # choose the splitter class
scores = cross_val_score(clone(estimator), features, labels, cv=splitter, scoring=scorer)
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
precision_score(y_true, predicted_labels)
recall_score(y_true, predicted_labels)
f1_score(y_true, predicted_labels)
roc_auc_score(y_true, positive_scores)
estimator.predict(frame)
estimator.predict_proba(frame)[:, 1]
table.groupby(group_field)[flag_field].mean()
series.div(other)
~~~

~~~python
import shap
explainer = shap.TreeExplainer(tree_estimator)
values = explainer.shap_values(encoded_rows)
from lime.lime_tabular import LimeTabularExplainer
explainer = LimeTabularExplainer(background, feature_names=names, class_names=classes,
                                mode="classification", random_state=seed)
item = explainer.explain_instance(encoded_row, probability_function, labels=(1,))
item.as_list(label=1)
~~~

~~~python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=reference_frame, current_data=current_frame)
result = report.as_dict()
# DataDriftTable result interface
table_result["drift_by_columns"]  # field of the DataDriftTable metric result
~~~
