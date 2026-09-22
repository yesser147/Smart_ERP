import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService } from '../../core/services/ai.service';

export interface ChartConfig {
  chart_type: 'bar' | 'line' | 'pie' | 'doughnut';
  title: string;
  labels: string[];
  datasets: { label: string; data: number[] }[];
}

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  data?: Record<string, any>[];
  chart?: ChartConfig;
}

@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ai-assistant.component.html'
})
export class AiAssistantComponent {
  private aiService = inject(AiService);

  isOpen = false;
  isLoading = false;
  userInput = '';
  messages: ChatMessage[] = [
    { sender: 'ai', text: 'Hi! How can I help you with HR or budget questions today?' }
  ];

  toggleAssistant(): void {
    this.isOpen = !this.isOpen;
  }

  sendMessage(): void {
    if (!this.userInput.trim()) return;

    const query = this.userInput.trim();
    this.messages.push({ sender: 'user', text: query });
    this.userInput = '';
    this.isLoading = true;

    this.aiService.askAssistant(query).subscribe({
      next: (res) => {
        this.messages.push({
          sender: 'ai',
          text: res.summary || 'Here is what I found.',
          data: res.tabular_data,
          chart: res.chart ?? undefined
        });
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages.push({ sender: 'ai', text: 'Sorry, something went wrong with that request.' });
        this.isLoading = false;
      }
    });
  }

  runBudgetAdvisor(): void {
    this.messages.push({ sender: 'user', text: 'Run a prescriptive budget analysis.' });
    this.isLoading = true;
    this.aiService.getBudgetAdvice().subscribe({
      next: (res) => {
        this.messages.push({ sender: 'ai', text: res.executive_proposal_memo || 'Budget analysis complete.' });
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages.push({ sender: 'ai', text: 'Sorry, the budget analysis failed.' });
        this.isLoading = false;
      }
    });
  }

  runRetentionAnalysis(): void {
    this.messages.push({ sender: 'user', text: 'Generate the macro retention strategy.' });
    this.isLoading = true;
    this.aiService.getRetentionStrategy().subscribe({
      next: (res) => {
        this.messages.push({ sender: 'ai', text: res.executive_summary || 'Retention analysis complete.' });
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages.push({ sender: 'ai', text: 'Sorry, the retention analysis failed.' });
        this.isLoading = false;
      }
    });
  }

  getKeys(obj: any): string[] {
    return obj && typeof obj === 'object' ? Object.keys(obj) : [];
  }

  /**
   * Converts the LLM's lightweight markdown (**bold**, *italic*, "- " bullets,
   * blank-line paragraphs) into safe HTML for [innerHTML]. Angular's default
   * sanitizer allows strong/em/ul/li/p/br, so no DomSanitizer bypass is needed.
   */
  formatMessage(text: string | undefined | null): string {
    if (!text) return '';

    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    html = html
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');

    const lines = html.split('\n');
    const out: string[] = [];
    let inList = false;

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (line.startsWith('- ')) {
        if (!inList) { out.push('<ul class="list-disc pl-4 space-y-0.5 mt-1">'); inList = true; }
        out.push(`<li>${line.slice(2)}</li>`);
      } else {
        if (inList) { out.push('</ul>'); inList = false; }
        if (line) out.push(`<p class="mt-1 first:mt-0">${line}</p>`);
      }
    }
    if (inList) out.push('</ul>');

    return out.join('');
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const container = document.getElementById('chat-container');
      if (container) container.scrollTop = container.scrollHeight;
    }, 100);
  }
}