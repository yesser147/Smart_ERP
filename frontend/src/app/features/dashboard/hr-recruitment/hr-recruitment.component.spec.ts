import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrRecruitmentComponent } from './hr-recruitment.component';

describe('HrRecruitmentComponent', () => {
  let component: HrRecruitmentComponent;
  let fixture: ComponentFixture<HrRecruitmentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrRecruitmentComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(HrRecruitmentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
