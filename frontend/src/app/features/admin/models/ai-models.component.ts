import { Component, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass } from '@angular/common';
import { AiService } from '../../../core/services/ai.service';
import { ModelsStatus } from '../../../core/models/ai.model';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { errorMessage } from '../../../shared/utils/errors';

interface Verdict { label: string; tone: string; text: string; }

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
    if (auc >= 0.75) return { label: 'Reliable', tone: 'emerald', text: 'Separates leavers from stayers well; the risk scores are usable to prioritise conversations.' };
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

  tone(t: string): string {
    return {
      emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
      amber: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
      rose: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
    }[t] ?? 'bg-slate-500/10 text-slate-300 border-slate-500/20';
  }
}
