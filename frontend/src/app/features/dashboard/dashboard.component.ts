import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { TokenService } from '../../core/services/token.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule,RouterModule],
  templateUrl:'./dashboard.component.html'
})
export class DashboardComponent {
  private authService = inject(AuthService);
  private tokenService = inject(TokenService);

  userInfo = this.tokenService.getUserInfo();

  logout(): void {
    this.authService.logout();
  }
}