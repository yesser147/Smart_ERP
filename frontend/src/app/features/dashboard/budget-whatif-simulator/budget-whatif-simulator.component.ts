import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, switchMap } from 'rxjs/operators';
import { AiService } from '../../../core/services/ai.service';
import { DepartmentBaseline, SimulationResult } from '../../../core/models/ai.model';

interface DeptSliderState extends DepartmentBaseline {
  sliderValue: number;
  simulated?: SimulationResult;
  loading: boolean;
}

@Component({
  selector: 'app-budget-whatif-simulator',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './budget-whatif-simulator.component.html',
  styleUrls: ['./budget-whatif-simulator.component.css']
})
export class BudgetWhatifSimulatorComponent implements OnInit {
  private aiService = inject(AiService);

  loading = true;
  error = false;
  departments: DeptSliderState[] = [];

  // The new money the user has to distribute. Separate from
  // currentTotalBudget (sum of what departments already have), which is
  // shown only for reference.
  availableBudget = 0;
  currentTotalBudget = 0;

  private sliderChange$ = new Map<number, Subject<number>>();

  ngOnInit(): void {
    this.loadBaselines();
  }

  loadBaselines(): void {
    this.loading = true;
    this.error = false;
    this.aiService.getDepartmentBaselines().subscribe({
      next: (baselines) => {
        this.departments = baselines.map(b => ({ ...b, sliderValue: b.current_budget, loading: false }));
        this.currentTotalBudget = this.departments.reduce((sum, d) => sum + d.current_budget, 0);
        this.departments.forEach(d => this.registerSlider(d.department_id));
        this.loading = false;
      },
      error: () => {
        this.error = true;
        this.loading = false;
      }
    });
  }

  private registerSlider(departmentId: number): void {
    const subject = new Subject<number>();
    this.sliderChange$.set(departmentId, subject);

    subject.pipe(
      debounceTime(250),
      switchMap(newBudget => {
        const dept = this.departments.find(d => d.department_id === departmentId)!;
        dept.loading = true;
        return this.aiService.simulateBudget(departmentId, newBudget);
      })
    ).subscribe({
      next: (result) => {
        const dept = this.departments.find(d => d.department_id === departmentId);
        if (dept) {
          dept.simulated = result;
          dept.loading = false;
        }
      },
      error: () => {
        const dept = this.departments.find(d => d.department_id === departmentId);
        if (dept) dept.loading = false;
      }
    });
  }

  /** Sum of every department's increase over its own current budget.
   * Decreasing a slider below its current budget frees pool room for
   * others (negative delta), rather than being wasted. */
  get totalAllocated(): number {
    return this.departments.reduce((sum, d) => sum + (d.sliderValue - d.current_budget), 0);
  }

  get remainingBudget(): number {
    return this.availableBudget - this.totalAllocated;
  }

  get isOverBudget(): boolean {
    // Should never actually trigger since onSliderChange clamps -- kept
    // as a safety indicator in case availableBudget itself is edited
    // to something inconsistent mid-drag.
    return this.totalAllocated > this.availableBudget + 0.01;
  }

  get allocationPercent(): number {
    if (this.availableBudget <= 0) return 0;
    return Math.min(100, Math.max(0, (this.totalAllocated / this.availableBudget) * 100));
  }

  private allocatedExcluding(departmentId: number): number {
    return this.departments
      .filter(d => d.department_id !== departmentId)
      .reduce((sum, d) => sum + (d.sliderValue - d.current_budget), 0);
  }

  /** Called on every drag. Clamps the requested value so the pool total
   * (sum of every department's increase) never exceeds availableBudget,
   * and never exceeds this department's own slider_min/slider_max. */
  onSliderChange(dept: DeptSliderState, rawValue: number): void {
    const otherAllocated = this.allocatedExcluding(dept.department_id);
    const maxWithinPool = dept.current_budget + (this.availableBudget - otherAllocated);

    const clamped = Math.min(rawValue, maxWithinPool, dept.slider_max);
    const finalValue = Math.max(clamped, dept.slider_min);

    dept.sliderValue = finalValue; // snaps the thumb back if the drag overshot the pool
    this.sliderChange$.get(dept.department_id)?.next(finalValue);
  }

  /** If the user shrinks the pool below what's already allocated, scale
   * every positive allocation down proportionally instead of leaving
   * now-invalid slider positions on screen. */
  onAvailableBudgetChange(): void {
    if (this.availableBudget < 0) this.availableBudget = 0;

    const totalIncrease = this.departments.reduce(
      (sum, d) => sum + Math.max(0, d.sliderValue - d.current_budget), 0
    );

    if (totalIncrease > this.availableBudget && totalIncrease > 0) {
      const scale = this.availableBudget / totalIncrease;
      this.departments.forEach(d => {
        const increase = Math.max(0, d.sliderValue - d.current_budget);
        const newValue = d.current_budget + increase * scale;
        d.sliderValue = newValue;
        this.sliderChange$.get(d.department_id)?.next(newValue);
      });
    }
  }

  resetAllocations(): void {
    this.departments.forEach(d => {
      d.sliderValue = d.current_budget;
      d.simulated = undefined;
    });
  }

  /** Maps a normalized performance value (0-1 within this department's
   * own curve range) to a topographic-style color: blue (low) -> green
   * -> amber -> red (high) -- the 'altitude' look along the track. */
  private terrainColor(t: number): string {
    const stops: { t: number; c: [number, number, number] }[] = [
      { t: 0.0, c: [59, 130, 246] },
      { t: 0.35, c: [16, 185, 129] },
      { t: 0.65, c: [245, 158, 11] },
      { t: 1.0, c: [239, 68, 68] }
    ];
    for (let i = 0; i < stops.length - 1; i++) {
      const a = stops[i], b = stops[i + 1];
      if (t >= a.t && t <= b.t) {
        const localT = (t - a.t) / (b.t - a.t || 1);
        const c = a.c.map((v, idx) => Math.round(v + (b.c[idx] - v) * localT));
        return `rgb(${c[0]},${c[1]},${c[2]})`;
      }
    }
    const last = stops[stops.length - 1].c;
    return `rgb(${last[0]},${last[1]},${last[2]})`;
  }

  trackGradient(dept: DeptSliderState): string {
    if (!dept.curve || dept.curve.length === 0) return 'transparent';
    const perfValues = dept.curve.map(p => p.performance);
    const min = Math.min(...perfValues);
    const max = Math.max(...perfValues);
    const range = (max - min) || 1;

    const stops = dept.curve.map(p => {
      const pct = (p.budget / dept.slider_max) * 100;
      const t = (p.performance - min) / range;
      return `${this.terrainColor(t)} ${pct.toFixed(1)}%`;
    });
    return `linear-gradient(to right, ${stops.join(', ')})`;
  }

  peakMarkerPosition(dept: DeptSliderState): number {
    if (!dept.peak_budget || !dept.slider_max) return 0;
    return (dept.peak_budget / dept.slider_max) * 100;
  }

  gainClass(gain: number | undefined): string {
    if (gain === undefined) return 'text-slate-400';
    return gain >= 0 ? 'text-teal-400' : 'text-rose-400';
  }
}