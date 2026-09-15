import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrCompensationComponent } from './hr-compensation.component';

describe('HrCompensationComponent', () => {
  let component: HrCompensationComponent;
  let fixture: ComponentFixture<HrCompensationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrCompensationComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(HrCompensationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
