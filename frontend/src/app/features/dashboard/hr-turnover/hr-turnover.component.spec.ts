import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrTurnoverComponent } from './hr-turnover.component';

describe('HrTurnoverComponent', () => {
  let component: HrTurnoverComponent;
  let fixture: ComponentFixture<HrTurnoverComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrTurnoverComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(HrTurnoverComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
