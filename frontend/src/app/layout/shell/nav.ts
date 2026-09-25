import { RoleName } from '../../core/models/auth.model';
import { HR_ROLES } from '../../core/guards/role.guard';

export interface NavItem {
  label: string;
  icon: string;
  link: string;
  roles?: RoleName[];        // missing = every signed-in user
  needsEmployee?: boolean;   // only for accounts linked to an employee file
  badge?: 'pendingLeave';
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

const ADMIN: RoleName[] = ['ROLE_ADMIN'];

/** The sidebar. Each route's title / group (for the breadcrumb) is in shell.routes.ts. */
export const NAV: NavGroup[] = [
  {
    label: 'Workspace',
    items: [
      { label: 'Overview', icon: 'squares', link: '/dashboard/overview', roles: HR_ROLES },
      { label: 'My space', icon: 'user-circle', link: '/dashboard/me', needsEmployee: true },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { label: 'Turnover', icon: 'arrow-path', link: '/dashboard/turnover', roles: HR_ROLES },
      { label: 'Compensation', icon: 'banknotes', link: '/dashboard/compensation', roles: HR_ROLES },
      { label: 'Recruitment & training', icon: 'chart-bar', link: '/dashboard/recruitment-analytics', roles: HR_ROLES },
    ],
  },
  {
    label: 'People',
    items: [
      { label: 'Employees', icon: 'users', link: '/dashboard/employees', roles: HR_ROLES },
      { label: 'Departments', icon: 'building', link: '/dashboard/departments', roles: HR_ROLES },
      { label: 'Leave requests', icon: 'calendar', link: '/dashboard/leave', roles: HR_ROLES, badge: 'pendingLeave' },
    ],
  },
  {
    label: 'Recruitment',
    items: [
      { label: 'Job openings', icon: 'briefcase', link: '/dashboard/jobs', roles: HR_ROLES },
      { label: 'Applicants', icon: 'inbox', link: '/dashboard/applicants', roles: HR_ROLES },
      { label: 'CV search', icon: 'document-search', link: '/dashboard/cv-search', roles: HR_ROLES },
    ],
  },
  {
    label: 'AI & strategy',
    items: [
      { label: 'Budget advisor', icon: 'cpu-chip', link: '/dashboard/budget', roles: HR_ROLES },
      { label: 'Retention strategy', icon: 'shield-check', link: '/dashboard/retention', roles: HR_ROLES },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Users & roles', icon: 'key', link: '/dashboard/admin/users', roles: ADMIN },
      { label: 'Audit log', icon: 'clipboard', link: '/dashboard/admin/audit', roles: ADMIN },
      { label: 'AI models', icon: 'sparkles', link: '/dashboard/admin/models', roles: ADMIN },
    ],
  },
];
