import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BudgetWhatifSimulatorComponent } from './budget-whatif-simulator.component';

describe('BudgetWhatifSimulatorComponent', () => {
  let component: BudgetWhatifSimulatorComponent;
  let fixture: ComponentFixture<BudgetWhatifSimulatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BudgetWhatifSimulatorComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(BudgetWhatifSimulatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
