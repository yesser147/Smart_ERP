import { Component, Input } from '@angular/core';
import { NgApexchartsModule } from 'ng-apexcharts';

@Component({
  selector: 'app-hr-compensation',
  standalone: true,
  imports: [NgApexchartsModule],
  templateUrl: './hr-compensation.component.html'
})
export class HrCompensationComponent {
  @Input() salaryChart: any;
  @Input() performanceChart: any;
  @Input() trainingChart: any;
  @Input() payGapChart: any;
}
