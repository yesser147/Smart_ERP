const FEATURE_LABELS: Record<string, string> = {
  tenure_days: 'Tenure',
  overtime: 'Overtime',
  job_function: 'Job role',
  department_type: 'Department',
  performance_score: 'Performance rating',
  num_companies_worked: 'Number of previous employers',
  years_with_curr_manager: 'Years with current manager',
  avg_engagement_score: 'Engagement (surveys)',
  avg_satisfaction_score: 'Satisfaction (surveys)',
  avg_work_life_balance: 'Work-life balance (surveys)',
  stock_option_level: 'Stock options',
  percent_salary_hike: 'Last salary raise',
};

/** ML feature name ("years_since_last_promotion") -> "Years since last promotion". */
export function featureLabel(name: string): string {
  if (FEATURE_LABELS[name]) return FEATURE_LABELS[name];
  const text = name.replace(/_/g, ' ').trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
}
