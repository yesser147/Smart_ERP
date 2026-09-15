import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApplicantCvManagerComponent } from './applicant-cv-manager.component';

describe('ApplicantCvManagerComponent', () => {
  let component: ApplicantCvManagerComponent;
  let fixture: ComponentFixture<ApplicantCvManagerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ApplicantCvManagerComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ApplicantCvManagerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
