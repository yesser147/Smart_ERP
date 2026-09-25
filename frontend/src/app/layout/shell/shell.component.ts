import { Component, DestroyRef, HostListener, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { ActivatedRoute, NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';

import { IconComponent } from '../../shared/components/icon/icon.component';
import { AiAssistantComponent } from '../../features/ai/ai-assistant/ai-assistant.component';
import { TokenService } from '../../core/services/token.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { BadgeService } from '../../core/services/badge.service';
import { HR_ROLES } from '../../core/guards/role.guard';
import { ROLE_LABELS } from '../../core/models/auth.model';
import { NotificationDTO } from '../../core/models/hr.model';
import { NAV, NavGroup, NavItem } from './nav';

const COLLAPSED_KEY = 'nexus_erp_sidebar_collapsed';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgClass, DatePipe, IconComponent, AiAssistantComponent],
  templateUrl: './shell.component.html'
})
export class ShellComponent implements OnInit, OnDestroy {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private tokenService = inject(TokenService);
  private authService = inject(AuthService);
  private badges = inject(BadgeService);
  private destroyRef = inject(DestroyRef);
  readonly notifications = inject(NotificationService);

  readonly user = this.tokenService.getUserInfo();
  readonly isHrUser = this.tokenService.hasAnyRole(HR_ROLES);
  readonly roleLabel = ROLE_LABELS[this.user?.role ?? ''] ?? '';
  readonly today = new Date();

  readonly collapsed = signal(this.readCollapsed());
  readonly mobileOpen = signal(false);
  readonly menu = signal<'notifications' | 'user' | null>(null);
  readonly crumb = signal<{ group: string; title: string }>({ group: '', title: '' });

  /** Only the groups / items this user may open. */
  readonly nav: NavGroup[] = NAV
    .map(g => ({ ...g, items: g.items.filter(i => this.canSee(i)) }))
    .filter(g => g.items.length > 0);

  readonly displayName = computed(() => {
    const email = this.user?.email ?? '';
    const local = email.split('@')[0] ?? '';
    return local.split(/[._-]/).filter(Boolean)
      .map(p => p[0].toUpperCase() + p.slice(1)).join(' ') || email;
  });

  readonly initials = computed(() => {
    const parts = this.displayName().split(' ');
    return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || '?';
  });

  ngOnInit(): void {
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(() => {
      this.updateCrumb();
      this.mobileOpen.set(false);
      this.menu.set(null);
    });
    this.updateCrumb();

    this.notifications.start();
    if (this.isHrUser) this.badges.refreshPendingLeave();
  }

  ngOnDestroy(): void {
    this.notifications.stop();
  }

  private canSee(item: NavItem): boolean {
    if (item.roles && !this.tokenService.hasAnyRole(item.roles)) return false;
    if (item.needsEmployee && !this.user?.employeeId) return false;
    return true;
  }

  badgeOf(item: NavItem): number {
    return item.badge === 'pendingLeave' ? this.badges.pendingLeave() : 0;
  }

  /** Breadcrumb = data of the deepest active route. */
  private updateCrumb(): void {
    let r = this.route;
    while (r.firstChild) r = r.firstChild;
    const data = r.snapshot.data;
    this.crumb.set({ group: data['group'] ?? '', title: data['title'] ?? '' });
  }

  toggleCollapsed(): void {
    this.collapsed.update(v => !v);
    try { localStorage.setItem(COLLAPSED_KEY, String(this.collapsed())); } catch { /* private mode */ }
    // charts measure their container: tell them once the transition is over
    setTimeout(() => window.dispatchEvent(new Event('resize')), 250);
  }

  private readCollapsed(): boolean {
    try { return localStorage.getItem(COLLAPSED_KEY) === 'true'; } catch { return false; }
  }

  toggleMenu(which: 'notifications' | 'user', event: Event): void {
    event.stopPropagation();
    this.menu.update(m => (m === which ? null : which));
  }

  @HostListener('document:click')
  closeMenus(): void {
    this.menu.set(null);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.menu.set(null);
    this.mobileOpen.set(false);
  }

  openNotification(n: NotificationDTO): void {
    this.notifications.markRead(n);
    this.menu.set(null);
    if (n.link) this.router.navigateByUrl(n.link);
  }

  logout(): void {
    this.notifications.stop();
    this.authService.logout();
  }
}
