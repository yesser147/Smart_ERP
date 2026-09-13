// employee-detail.component.ts
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { HrService } from '../../../core/services/hr.service';
import { EmployeeDTO } from '../../../core/models/hr.model';

@Component({
  selector: 'app-employee-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './employee-detail.component.html'
})
export class EmployeeDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private hrService = inject(HrService);

  employee: EmployeeDTO | null = null;
  loading = true;
  error = false;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.hrService.getEmployeeById(id).subscribe({
      next: (e) => { this.employee = e; this.loading = false; },
      error: () => { this.error = true; this.loading = false; }
    });
  }
}