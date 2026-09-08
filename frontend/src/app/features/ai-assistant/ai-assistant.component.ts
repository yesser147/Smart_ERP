import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiService } from '../../core/services/ai.service';

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  data?: Record<string, any>[];
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
    { sender: 'ai', text: 'Bonjour ! Comment puis-je vous aider avec les RH ou le budget aujourd\'hui ?' }
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
          text: res.summary || 'Voici ce que j\'ai trouvé.',
          data: res.tabular_data
        });
        this.isLoading = false;
        this.scrollToBottom();
      },
      error: () => {
        this.messages.push({ sender: 'ai', text: 'Désolé, une erreur s\'est produite lors de la requête.' });
        this.isLoading = false;
      }
    });
  }

  runBudgetAdvisor(): void {
    this.messages.push({ sender: 'user', text: 'Lance une analyse de budget prescriptive.' });
    this.isLoading = true;
    this.aiService.getBudgetAdvice().subscribe(res => {
      this.messages.push({ sender: 'ai', text: res.executive_proposal_memo || 'Analyse budgétaire terminée.' });
      this.isLoading = false;
    });
  }

  runRetentionAnalysis(): void {
    this.messages.push({ sender: 'user', text: 'Génère la stratégie macro de rétention.' });
    this.isLoading = true;
    this.aiService.getRetentionStrategy().subscribe(res => {
      this.messages.push({ sender: 'ai', text: res.executive_summary || 'Analyse de rétention terminée.' });
      this.isLoading = false;
    });
  }

  getKeys(obj: any): string[] {
    return obj && typeof obj === 'object' ? Object.keys(obj) : [];
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const container = document.getElementById('chat-container');
      if (container) container.scrollTop = container.scrollHeight;
    }, 100);
  }
}