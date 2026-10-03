import { Component, ElementRef, HostListener, ViewChild, inject } from '@angular/core';
import { NgClass, SlicePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService } from '../../../core/services/ai.service';
import { PinnedChartsService } from '../../../core/services/pinned-charts.service';
import { ChartSpec, PopularQuestion } from '../../../core/models/ai.model';
import { IconComponent } from '../../../shared/components/icon/icon.component';
import { AiChartComponent } from '../../../shared/components/ai-chart/ai-chart.component';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { saveFile, toCsv } from '../../../shared/utils/download';
import { errorMessage } from '../../../shared/utils/errors';

interface Message {
  sender: 'user' | 'ai';
  text: string;
  question?: string;
  sql?: string;
  data?: Record<string, unknown>[];
  /** the chart chosen by the AI: sent with the answer when the question asks for one,
   *  or later with the "Create a chart" button */
  spec?: ChartSpec | null;
  chartState?: 'loading' | string;   // a string = why no chart could be drawn
  showAll?: boolean;
  pin?: 'saving' | 'pinned' | string;   // a string = the error message
}

const DEFAULT_QUESTIONS = [
  'How many active employees are there per department?',
  'Average salary by department and gender',
  'Show turnover by department as a pie chart',
  'How many applications did we receive per open job?',
];

/** Floating HR assistant: question in plain language -> SQL -> table, chart chosen by
 *  the AI, and a written answer streamed word by word. Charts can be pinned to the dashboard. */
@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [NgClass, SlicePipe, FormsModule, IconComponent, AiChartComponent, MarkdownPipe],
  templateUrl: './ai-assistant.component.html'
})
export class AiAssistantComponent {
  private ai = inject(AiService);
  private pinned = inject(PinnedChartsService);

  @ViewChild('scroll') scroll?: ElementRef<HTMLElement>;

  /** Server-side memory is kept per conversation. */
  private conversationId = globalThis.crypto?.randomUUID?.() ?? `c-${Date.now()}-${Math.random()}`;

  isOpen = false;
  isLoading = false;
  busy = false;
  userInput = '';
  suggestions: string[] = DEFAULT_QUESTIONS;
  private suggestionsLoaded = false;
  /** the message whose chart is shown in the large view */
  expanded: Message | null = null;
  messages: Message[] = [
    { sender: 'ai', text: 'Hi! Ask me anything about your workforce data. Want a chart? Say so in the question ("as a pie chart", "plot it per year"...) or click **Create a chart** under a table.' }
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

  @HostListener('document:keydown.escape')
  closeExpanded(): void {
    this.expanded = null;
  }

  send(text?: string): void {
    const query = (text ?? this.userInput).trim();
    if (!query || this.busy) return;
    this.messages.push({ sender: 'user', text: query });
    this.userInput = '';
    this.isLoading = true;        // typing dots until the first words arrive
    this.busy = true;             // no new question until this answer is complete
    this.scrollDown();

    let reply: Message | null = null;
    const ensureReply = (): Message => {
      if (!reply) {
        reply = { sender: 'ai', text: '', question: query };
        this.messages.push(reply);
      }
      return reply;
    };

    this.ai.askAssistant(query, this.conversationId).subscribe({
      next: ev => {
        const m = ensureReply();
        if (ev.type === 'data') {
          m.data = ev.tabular_data;
          m.sql = ev.sql_query;
        } else if (ev.type === 'chart') {
          m.spec = ev.chart;
        } else if (ev.type === 'text') {
          m.text += ev.text;
          this.isLoading = false;
        } else if (ev.type === 'error') {
          m.text += (m.text ? '\n\n' : '') + ev.message;
        }
        this.scrollDown();
      },
      error: err => {
        ensureReply().text = err?.message || 'Sorry, something went wrong with that question.';
        this.isLoading = this.busy = false;
        this.scrollDown();
      },
      complete: () => {
        const m = ensureReply();
        if (!m.text) m.text = 'Here is what I found.';
        this.isLoading = this.busy = false;
      }
    });
  }

  chartTitle(m: Message): string {
    return m.spec?.title || m.question || 'Chart';
  }

  createChart(m: Message): void {
    if (!m.sql || m.chartState === 'loading') return;
    m.chartState = 'loading';
    this.ai.chartForAnswer(m.question ?? '', m.sql).subscribe({
      next: res => { m.spec = res.chart; m.chartState = undefined; this.scrollDown(); },
      error: err => m.chartState = errorMessage(err, 'No chart could be drawn for this result.')
    });
  }

  chartError(m: Message): string | null {
    return m.chartState && m.chartState !== 'loading' ? m.chartState : null;
  }

  pin(m: Message): void {
    if (!m.spec || !m.sql || m.pin === 'saving' || m.pin === 'pinned') return;
    m.pin = 'saving';
    this.pinned.pin({ title: this.chartTitle(m), question: m.question ?? '', sql_query: m.sql, chart: m.spec }).subscribe({
      next: () => m.pin = 'pinned',
      error: err => m.pin = errorMessage(err, 'The chart could not be pinned.')
    });
  }

  pinError(m: Message): string | null {
    return m.pin && m.pin !== 'saving' && m.pin !== 'pinned' ? m.pin : null;
  }

  /** decimals shortened for reading (the CSV keeps the exact values) */
  cell(v: unknown): unknown {
    return typeof v === 'number' && !Number.isInteger(v) ? Math.round(v * 100) / 100 : v;
  }

  keys(row: Record<string, unknown> | undefined): string[] {
    return row ? Object.keys(row) : [];
  }

  download(m: Message): void {
    if (!m.data?.length) return;
    saveFile(toCsv(m.data, this.keys(m.data[0]).map(k => ({ key: k, label: k }))), 'assistant-result.csv');
  }

  private scrollDown(): void {
    setTimeout(() => {
      const el = this.scroll?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
}
