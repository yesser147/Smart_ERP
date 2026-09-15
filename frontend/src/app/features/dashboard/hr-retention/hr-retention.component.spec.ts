import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HrRetentionComponent } from './hr-retention.component';

describe('HrRetentionComponent', () => {
  let component: HrRetentionComponent;
  let fixture: ComponentFixture<HrRetentionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HrRetentionComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(HrRetentionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
