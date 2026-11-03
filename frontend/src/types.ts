export type Transaction = {
  Transaction_ID: string;
  Transaction_Date: string;
  Transaction_Amount: number;
  Merchant_Category: string;
  Payment_Method: string;
  Device_Type: string;
  Location: string;
  Account_Age_Days: number | null;
  Is_International: number;
  Fraudulent: number;
  fraud_probability: number;
  risk_score: number;
  risk_category: string;
  predicted_class: number;
  evaluation_cohort: string;
};
export type Explanation = {
  method: string;
  output_space: string;
  note: string;
  base_value: number;
  explained_output: number;
  factors: {
    feature: string;
    contribution: number;
    transformed_value: number;
  }[];
};
export type Prediction = {
  fraud_probability: number;
  risk_score: number;
  predicted_class: number;
  risk_category: string;
  threshold: number;
  model_version: string;
  warnings: string[];
  explanation: Explanation | null;
};
export type Overview = {
  total_transactions: number;
  fraudulent_transactions: number;
  fraud_rate: number;
  total_value: number;
  observed_fraud_value: number;
  estimated_exposure: number;
  average_amount: number;
  flagged_transactions: number;
  date_start: string;
  date_end: string;
  recent_fraud: Transaction[];
  note: string;
};
export type Group = {
  name: string;
  transactions: number;
  fraud: number;
  fraud_rate: number;
  flagged: number;
  value: number;
  fraud_value?: number;
  high_risk?: number;
};
export type Analytics = {
  monthly: Group[];
  by_type: Group[];
  by_location: Group[];
  by_amount: Group[];
  by_payment: Group[];
  probability_distribution: { name: string; count: number }[];
};
export type ModelInfo = {
  model_name: string;
  model_version: string;
  training_date: string;
  threshold: number;
  trained_threshold: number;
  risk_boundaries: number[];
  categories: Record<string, string[]>;
  selection_reason: string;
  limitations: string[];
  features: string[];
  split_windows: Record<
    string,
    { rows: number; fraud: number; start: string; end: string }
  >;
  dataset_version: string;
  libraries: Record<string, string>;
  training_config: Record<string, number>;
};
export type MetricValues = Record<string, number> & {
  confusion_matrix: number[][];
};
export type Metrics = {
  test_metrics: MetricValues;
  constant_baseline_test: MetricValues;
  test_uncertainty: { pr_auc_95_percentile_interval: number[] };
  model_comparison: {
    model: string;
    tuning_pr_auc: number;
    policy_metrics: MetricValues;
  }[];
  curves: { pr: { x: number; y: number }[]; roc: { x: number; y: number }[] };
  threshold_analysis: {
    threshold: number;
    estimated_cost: number;
    review_rate: number;
    precision: number;
    recall: number;
  }[];
  global_explanations: { feature: string; mean_absolute_shap: number }[];
  note: string;
};
