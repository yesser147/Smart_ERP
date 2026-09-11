import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CandidateMatchComponent } from './candidate-match.component';

describe('CandidateMatchComponent', () => {
  let component: CandidateMatchComponent;
  let fixture: ComponentFixture<CandidateMatchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CandidateMatchComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(CandidateMatchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
