import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import { DepartmentTurnoverDTO } from '../../../core/models/analytics.model';

@Component({
  selector: 'app-hr-turnover',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule],
  templateUrl: './hr-turnover.component.html'
})
export class HrTurnoverComponent {
  @Input() turnoverChart: any;
  @Input() turnoverTypeChart: any;
  @Input() rawTurnoverData: DepartmentTurnoverDTO[] = [];
}