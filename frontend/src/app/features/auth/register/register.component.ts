import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { RoleName } from '../../../core/models/auth.model';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.component.html'
})
export class RegisterComponent {
  private fb = inject(NonNullableFormBuilder);
  private authService = inject(AuthService);

  isLoading = signal<boolean>(false);
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);

  roles: { label: string; value: RoleName }[] = [
    { label: 'Administrateur', value: 'ROLE_ADMIN' },
    { label: 'Responsable RH', value: 'ROLE_HR_MANAGER' },
    { label: 'Employé', value: 'ROLE_EMPLOYEE' }
  ];

  registerForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    role: ['ROLE_EMPLOYEE' as RoleName, [Validators.required]]
  });

  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    this.authService.createUser(this.registerForm.getRawValue()).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.successMessage.set(`Utilisateur ${res.email} créé avec succès!`);
        this.registerForm.reset({ role: 'ROLE_EMPLOYEE' });
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.message || 'Erreur lors de la création de l\'utilisateur.');
      }
    });
  }
}