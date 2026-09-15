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
}