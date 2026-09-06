// hr-compensation.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';

@Component({
  selector: 'app-hr-compensation',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-compensation.component.html'
})
export class HrCompensationComponent {
  @Input() salaryChart: any;
  @Input() performanceChart: any;
  @Input() trainingChart: any;
}