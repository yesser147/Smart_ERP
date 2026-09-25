import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { NgClass, SlicePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgApexchartsModule } from 'ng-apexcharts';
import { AiService } from '../../../core/services/ai.service';
import { PopularQuestion } from '../../../core/models/ai.model';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { DARK_CHART, GRID, PALETTE } from '../../../shared/utils/chart-theme';
import { saveFile, toCsv } from '../../../shared/utils/download';
import { errorMessage } from '../../../shared/utils/errors';

interface Message {
  sender: 'user' | 'ai';
  text: string;
  data?: Record<string, unknown>[];
  chart?: any;
  showAll?: boolean;
}

const DEFAULT_QUESTIONS = [
  'How many active employees are there per department?',
  'What is the average salary by department?',
  'Which job titles have the highest turnover?',
  'How many applications did we receive per open job?',
];

/** Floating HR assistant: questions in plain language -> SQL -> answer, table and chart. */
@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [NgClass, SlicePipe, FormsModule, NgApexchartsModule, IconComponent, MarkdownPipe],
  templateUrl: './ai-assistant.component.html'
})
export class AiAssistantComponent {
  private ai = inject(AiService);

  @ViewChild('scroll') scroll?: ElementRef<HTMLElement>;

  /** Server-side memory is kept per conversation. */
  private conversationId = globalThis.crypto?.randomUUID?.() ?? `c-${Date.now()}-${Math.random()}`;

  isOpen = false;
  isLoading = false;
  userInput = '';
  suggestions: string[] = DEFAULT_QUESTIONS;
  private suggestionsLoaded = false;
  messages: Message[] = [
    { sender: 'ai', text: 'Hi! Ask me anything about your workforce data: headcount, salaries, turnover, recruitment...' }
  ];

  toggle(): void {
    this.isOpen = !this.isOpen;
    if (this.isOpen && !this.suggestionsLoaded) {
      this.suggestionsLoaded = true;
      this.ai.popularQuestions().subscribe({
        next: (list: PopularQuestion[]) => {
          if (list.length >= 2) this.suggestions = list.map(q => q.question).slice(0, 4);
        },
        error: () => { /* keep the defaults */ }
      });
    }
  }

  send(text?: string): void {
    const query = (text ?? this.userInput).trim();
    if (!query || this.isLoading) return;
    this.messages.push({ sender: 'user', text: query });
    this.userInput = '';
    this.isLoading = true;
    this.scrollDown();

    this.ai.askAssistant(query, this.conversationId).subscribe({
      next: res => {
        this.messages.push({
          sender: 'ai',
          text: res.summary || 'Here is what I found.',
          data: res.tabular_data ?? undefined,
          chart: this.autoChart(res.tabular_data),
        });
        this.isLoading = false;
        this.scrollDown();
      },
      error: err => {
        this.messages.push({ sender: 'ai', text: errorMessage(err, 'Sorry, something went wrong with that question.') });
        this.isLoading = false;
        this.scrollDown();
      }
    });
  }

  keys(row: Record<string, unknown> | undefined): string[] {
    return row ? Object.keys(row) : [];
  }

  download(m: Message): void {
    if (!m.data?.length) return;
    saveFile(toCsv(m.data, this.keys(m.data[0]).map(k => ({ key: k, label: k }))), 'assistant-result.csv');
  }

  /** A bar chart when the result is "one label column + numeric columns" with 2 to 25 rows. */
  private autoChart(rows: Record<string, unknown>[] | undefined): any {
    if (!rows || rows.length < 2 || rows.length > 25) return undefined;
    const keys = Object.keys(rows[0]);
    const isNum = (k: string) => rows.every(r => r[k] === null || typeof r[k] === 'number');
    const numeric = keys.filter(isNum).filter(k => !/(^|_)id$/i.test(k));
    const labels = keys.filter(k => !isNum(k));
    if (labels.length !== 1 || numeric.length < 1 || numeric.length > 3) return undefined;

    return {
      series: numeric.map(k => ({ name: k.replace(/_/g, ' '), data: rows.map(r => Number(r[k] ?? 0)) })),
      chart: { type: 'bar', height: 220, ...DARK_CHART },
      xaxis: { categories: rows.map(r => String(r[labels[0]] ?? '')), labels: { rotate: -45, trim: true, maxHeight: 80, style: { fontSize: '10px' } } },
      colors: PALETTE,
      plotOptions: { bar: { borderRadius: 3, columnWidth: '55%' } },
      dataLabels: { enabled: false },
      grid: GRID,
      legend: { show: numeric.length > 1, labels: { colors: '#94a3b8' } },
      tooltip: { theme: 'dark' },
    };
  }

  private scrollDown(): void {
    setTimeout(() => {
      const el = this.scroll?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
}
