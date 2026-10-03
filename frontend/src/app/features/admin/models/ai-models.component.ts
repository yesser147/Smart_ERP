import { Component, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass } from '@angular/common';
import { AiService } from '../../../core/services/ai.service';
import { ModelsStatus } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

interface Verdict { label: string; tone: string; text: string; }

/** One score explained for a non-specialist. */
export interface Explained {
  name: string;
  value: string;
  meaning: string;
  best: string;
  why: string;
  tone: 'good' | 'fair' | 'weak';
}

const pct = (v: number | null | undefined) => (v == null ? '—' : `${Math.round(v * 100)}%`);
const num = (v: number | null | undefined, d = 2) => (v == null ? '—' : Number(v).toFixed(d));

/** Model monitoring: quality of the ML models and a retrain button. */
@Component({
  selector: 'app-ai-models',
  standalone: true,
  imports: [DatePipe, DecimalPipe, NgClass, PageHeaderComponent, IconComponent],
  templateUrl: './ai-models.component.html'
})
export class AiModelsComponent implements OnInit {
  private ai = inject(AiService);

  status: ModelsStatus | null = null;
  loading = true;
  error: string | null = null;
  retraining = false;
  retrainMessage: string | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.ai.modelsStatus().subscribe({
      next: s => { this.status = s; this.loading = false; this.retraining = s.training; },
      error: err => { this.error = errorMessage(err, 'The AI engine is not reachable.'); this.loading = false; }
    });
  }

  retrain(): void {
    if (!confirm('Retrain both models on the current database? It takes about a minute.')) return;
    this.retraining = true;
    this.retrainMessage = null;
    this.error = null;
    this.ai.retrainModels().subscribe({
      next: s => {
        this.status = s;
        this.retraining = false;
        this.retrainMessage = 'Both models were retrained; every page now uses the new versions.';
      },
      error: err => {
        this.retraining = false;
        this.error = errorMessage(err, 'Retraining failed.');
      }
    });
  }

  get retention() { return this.status?.retention.metrics ?? null; }
  get budget() { return this.status?.budget.metrics ?? null; }

  get retentionVerdict(): Verdict {
    const auc = this.retention?.['cv_auc'];
    if (auc == null) return { label: 'Not trained', tone: 'slate', text: 'Train the model to see its quality.' };
    if (auc >= 0.75) return { label: 'Reliable', tone: 'emerald', text: 'Good at telling who is more likely to leave. Use the scores to decide whom to talk to first, never as a decision on its own.' };
    if (auc >= 0.65) return { label: 'Fair', tone: 'amber', text: 'Better than chance but noisy: treat the scores as indicative.' };
    return { label: 'Weak', tone: 'rose', text: 'Barely better than chance: do not rely on individual scores.' };
  }

  get budgetVerdict(): Verdict {
    const r2 = this.budget?.['cv_r2'];
    if (r2 == null) return { label: 'Not trained', tone: 'slate', text: 'Train the model to see its quality.' };
    if (r2 >= 0.5) return { label: 'Reliable', tone: 'emerald', text: 'Explains most of the variation in team performance.' };
    if (r2 > 0) return { label: 'Weak', tone: 'amber', text: 'Explains a small part of the variation: the simulator shows trends, not forecasts.' };
    return {
      label: 'No predictive power', tone: 'rose',
      text: 'On unseen teams it predicts worse than the average: in this data, training budget does not explain performance. The simulator is a demonstration only.'
    };
  }

  /** The attrition model's scores, in plain words. */
  get retentionScores(): Explained[] {
    const m = this.retention;
    if (!m) return [];
    const p = m['threshold_precision'], r = m['threshold_recall'];
    const f1 = p && r ? (2 * p * r) / (p + r) : null;
    const t = m['risk_threshold'];
    return [
      {
        name: 'Ranking quality (ROC AUC)', value: num(m['cv_auc']), tone: m['cv_auc'] >= 0.75 ? 'good' : 'fair',
        meaning: `Take one person who left and one who stayed at random: in ${pct(m['cv_auc'])} of the cases the model gives the higher risk to the one who left. 0.50 = tossing a coin.`,
        best: '1.00 would be perfect. Above 0.80 is considered good for people data.',
        why: 'Leaving a job also depends on things no database contains: a job offer elsewhere, a move, family, health, a conflict with a manager. No model can see those, so 1.00 is impossible.',
      },
      {
        name: 'Precision of the alerts', value: pct(p), tone: p >= 0.5 ? 'good' : 'fair',
        meaning: `Of 100 employees flagged "high risk", about ${Math.round((p ?? 0) * 100)} really left in the past data. The others looked similar but stayed.`,
        best: '100% would mean no false alarm.',
        why: `Only ${pct(m['churn_rate'])} of employees leave, so a rare event is hard to catch without false alarms. A false alarm costs little here: it means an unnecessary conversation with an employee.`,
      },
      {
        name: 'Recall (leavers caught)', value: pct(r), tone: r >= 0.5 ? 'good' : 'fair',
        meaning: `Of 100 employees who really left, the alert would have flagged about ${Math.round((r ?? 0) * 100)} of them in advance.`,
        best: '100% would mean nobody leaves without warning.',
        why: 'Precision and recall pull in opposite directions: lowering the alert threshold catches more leavers but gives more false alarms. The threshold below is the best balance of the two.',
      },
      {
        name: 'Balance of the two (F1)', value: num(f1), tone: (f1 ?? 0) >= 0.5 ? 'good' : 'fair',
        meaning: 'One number that combines precision and recall; it is only high when both are high.',
        best: '1.00. On this kind of data, 0.50 to 0.60 is a usual result.',
        why: 'Same reasons as above: rare event and missing information.',
      },
      {
        name: 'Alert threshold', value: pct(t), tone: 'good',
        meaning: `An employee is flagged "high risk" when the model gives a probability of ${pct(t)} or more. It looks low, but only ${pct(m['churn_rate'])} of people leave, so ${pct(t)} is already about twice the normal risk.`,
        best: 'There is no "best" value: it is chosen automatically at training time as the best balance between precision and recall.',
        why: '—',
      },
      {
        name: 'Detection of leavers (PR AUC)', value: num(m['cv_pr_auc']), tone: m['cv_pr_auc'] >= 2 * m['churn_rate'] ? 'good' : 'fair',
        meaning: `Measures the alerts at every possible threshold at once. Guessing at random would score ${num(m['churn_rate'])} (the share of leavers); the model scores ${num(m['cv_pr_auc'])}, about ${Math.round(m['cv_pr_auc'] / m['churn_rate'])} times better.`,
        best: '1.00.',
        why: 'This score is always low for rare events; what matters is how far it is above chance.',
      },
      {
        name: 'Simple model for comparison', value: num(m['baseline_cv_auc']), tone: 'fair',
        meaning: 'The same ranking score for a much simpler model (logistic regression), to check that the advanced model (XGBoost) is worth it.',
        best: 'The advanced model should normally be higher.',
        why: "Here both are about equal: the links in this data are simple (overtime, job level, stock options...). We keep XGBoost because it explains each person's risk (the 'what raises the risk' list on the employee file).",
      },
    ];
  }

  /** The budget model's scores, in plain words. */
  get budgetScores(): Explained[] {
    const m = this.budget;
    if (!m) return [];
    return [
      {
        name: 'Share of performance explained (R²)', value: num(m['cv_r2']), tone: m['cv_r2'] > 0.3 ? 'good' : 'weak',
        meaning: 'How much of the differences in team performance the model explains from the budget and team data. 0 = no better than always predicting the average; below 0 = worse than the average.',
        best: '1.00 would explain everything; 0.50 or more is useful.',
        why: 'In the IBM data the performance rating is almost always 3 or 4, and the training cost per team comes from a price list, so there is almost nothing to learn. With real company data (real budgets and varied ratings) this can improve.',
      },
      {
        name: 'Average error', value: num(m['cv_mae'], 3), tone: m['cv_mae'] < m['target_std'] / 2 ? 'good' : 'weak',
        meaning: `On average the prediction is off by ${num(m['cv_mae'], 3)} rating points, while team averages themselves only vary by about ${num(m['target_std'], 3)}.`,
        best: '0 would be exact. It should be much smaller than the natural variation.',
        why: 'The error is about as large as the variation: the model cannot tell good teams from others.',
      },
      {
        name: 'Teams used', value: `${m['n_rows']}`, tone: m['n_rows'] >= 200 ? 'good' : 'fair',
        meaning: `One example per team with at least ${m['min_headcount']} people.`,
        best: 'Several hundred examples (e.g. several years of budgets per team).',
        why: 'A company only has so many teams; collecting a budget per team and per year would multiply the examples.',
      },
    ];
  }

  explainedTone(t: Explained['tone']): string {
    return t === 'good' ? 'text-emerald-300' : t === 'fair' ? 'text-amber-300' : 'text-rose-300';
  }

  tone(t: string): string {
    return {
      emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
      amber: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
      rose: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
    }[t] ?? 'bg-slate-500/10 text-slate-300 border-slate-500/20';
  }
}
