import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AiService } from '../../../core/services/ai.service';

@Component({
  selector: 'app-hr-retention',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hr-retention.component.html'
})
export class HrRetentionComponent implements OnInit {
  private aiService = inject(AiService);

  loading = true;
  error = false;
  data: any = null;
  showQualityDetails = false;

  ngOnInit(): void {
    this.fetchRetentionStrategy();
  }

  fetchRetentionStrategy(): void {
    this.loading = true;
    this.error = false;

    this.aiService.getRetentionStrategy().subscribe({
      next: (res) => {
        this.data = res;
        this.loading = false;
      },
      error: () => {
        this.error = true;
        this.loading = false;
      }
    });
  }

  /** Converts the LLM's lightweight markdown (**bold**, *italic*, "- " bullets,
   *  blank-line paragraphs) into safe HTML for [innerHTML]. Angular's default
   *  sanitizer allows strong/em/ul/li/p, so no DomSanitizer bypass is needed.
   *  Kept in sync with the identical method in the other AI components. */
  formatMemo(text: string | undefined | null): string {
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
        if (!inList) { out.push('<ul class="list-disc pl-5 space-y-1">'); inList = true; }
        out.push(`<li>${line.slice(2)}</li>`);
      } else {
        if (inList) { out.push('</ul>'); inList = false; }
        if (line) out.push(`<p class="mt-2 first:mt-0">${line}</p>`);
      }
    }
    if (inList) out.push('</ul>');

    return out.join('');
  }
}