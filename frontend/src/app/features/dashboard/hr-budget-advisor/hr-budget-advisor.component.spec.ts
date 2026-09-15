import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrBudgetAdvisorComponent } from './hr-budget-advisor.component';

describe('HrBudgetAdvisorComponent', () => {
  let component: HrBudgetAdvisorComponent;
  let fixture: ComponentFixture<HrBudgetAdvisorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrBudgetAdvisorComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(HrBudgetAdvisorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
