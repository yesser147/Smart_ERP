import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-set-password',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div class="bg-slate-800 border border-slate-700 p-8 rounded-xl max-w-md w-full shadow-2xl">
        <h2 class="text-2xl font-bold text-teal-400 mb-2">Nexus ERP</h2>
        <p class="text-slate-400 mb-6">Définissez votre nouveau mot de passe pour finaliser l'activation de votre compte.</p>

        <form (ngSubmit)="onSubmit()" #f="ngForm">
          <div class="mb-4">
            <label class="block text-slate-300 mb-2">Nouveau mot de passe</label>
            <input type="password" [(ngModel)]="password" name="password" required minlength="6"
                   class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-teal-500">
          </div>

          <div class="mb-6">
            <label class="block text-slate-300 mb-2">Confirmer le mot de passe</label>
            <input type="password" [(ngModel)]="confirmPassword" name="confirmPassword" required
                   class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-teal-500">
          </div>

          <p *ngIf="errorMessage" class="text-red-400 text-sm mb-4">{{ errorMessage }}</p>
          <p *ngIf="successMessage" class="text-emerald-400 text-sm mb-4">{{ successMessage }}</p>

          <button type="submit" [disabled]="!f.valid || isLoading"
                  class="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-3 rounded-lg transition-colors">
            {{ isLoading ? 'Validation...' : 'Valider et continuer' }}
          </button>
        </form>
      </div>
    </div>
  `
})
export class SetPasswordComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);
  private service= inject(AuthService)

  token: string = '';
  password: string = '';
  confirmPassword: string = '';
  errorMessage: string = '';
  successMessage: string = '';
  isLoading: boolean = false;

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
      console.log('>>> Captured Token from URL:', this.token);
    });
  
    if (!this.token) {
      this.errorMessage = 'Jeton d\'activation manquant.';
    }
  }

  onSubmit(): void {
    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Les mots de passe ne correspondent pas.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    

    this.service.setpassword({
    token: this.token,
    newPassword: this.password
  }).subscribe({
    next: (response: string) => {
      this.isLoading = false;
      this.successMessage = 'Mot de passe configuré avec succès ! Redirection vers la page de connexion...';
      
      // Redirect user to login after 2 seconds
      setTimeout(() => {
        this.router.navigate(['/auth/login']);
      }, 2000);
    },
    error: (err) => {
      this.isLoading = false;
      
      // Handle error payload from GlobalExceptionHandler
      if (err.error) {
        try {
          const parsed = typeof err.error === 'string' ? JSON.parse(err.error) : err.error;
          this.errorMessage = parsed.message || 'Impossible de configurer le mot de passe.';
        } catch (e) {
          this.errorMessage = typeof err.error === 'string' ? err.error : 'Une erreur est survenue.';
        }
      } else {
        this.errorMessage = 'Impossible de contacter le serveur backend.';
      }
    }
  });
  }
}