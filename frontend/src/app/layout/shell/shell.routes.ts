import { Routes } from '@angular/router';
import { HR_ROLES, homeRedirectGuard, roleGuard } from '../../core/guards/role.guard';

const hr = [roleGuard(HR_ROLES)];
const admin = [roleGuard(['ROLE_ADMIN'])];

const ANALYTICS_TITLES = {
  overview: 'Overview',
  turnover: 'Turnover',
  compensation: 'Compensation & performance',
  'recruitment-analytics': 'Recruitment & training',
} as const;

/** Everything behind the login, inside the sidebar layout. `data` feeds the breadcrumb. */
export const SHELL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./shell.component').then(m => m.ShellComponent),
    children: [
      { path: '', pathMatch: 'full', canActivate: [homeRedirectGuard], children: [] },

      // ---- analytics: one component, four views sharing one cached data load
      ...(Object.keys(ANALYTICS_TITLES) as (keyof typeof ANALYTICS_TITLES)[]).map(view => ({
        path: view,
        canActivate: hr,
        data: { view, group: view === 'overview' ? 'Workspace' : 'Analytics', title: ANALYTICS_TITLES[view] },
        loadComponent: () => import('../../features/analytics/analytics-page/analytics-page.component').then(m => m.AnalyticsPageComponent)
      })),

      // ---- people
      { path: 'employees', canActivate: hr, data: { group: 'People', title: 'Employees' },
        loadComponent: () => import('../../features/people/employee-list/employee-list.component').then(m => m.EmployeeListComponent) },
      { path: 'employee/:id', canActivate: hr, data: { group: 'People', title: 'Employee file' },
        loadComponent: () => import('../../features/people/employee-detail/employee-detail.component').then(m => m.EmployeeDetailComponent) },
      { path: 'departments', canActivate: hr, data: { group: 'People', title: 'Departments' },
        loadComponent: () => import('../../features/people/department-list/department-list.component').then(m => m.DepartmentListComponent) },
      { path: 'department-type/:type', canActivate: hr, data: { group: 'People', title: 'Department' },
        loadComponent: () => import('../../features/people/department-type-detail/department-type-detail.component').then(m => m.DepartmentTypeDetailComponent) },
      { path: 'departments/:id', canActivate: hr, data: { group: 'People', title: 'Team' },
        loadComponent: () => import('../../features/people/department-detail/department-detail.component').then(m => m.DepartmentDetailComponent) },
      { path: 'leave', canActivate: hr, data: { group: 'People', title: 'Leave requests' },
        loadComponent: () => import('../../features/people/leave-approvals/leave-approvals.component').then(m => m.LeaveApprovalsComponent) },

      // ---- recruitment
      { path: 'jobs', canActivate: hr, data: { group: 'Recruitment', title: 'Job openings' },
        loadComponent: () => import('../../features/recruitment/job-openings/job-openings.component').then(m => m.JobOpeningsComponent) },
      { path: 'jobs/new', canActivate: hr, data: { group: 'Recruitment', title: 'New job opening' },
        loadComponent: () => import('../../features/recruitment/job-create/job-create.component').then(m => m.JobCreateComponent) },
      { path: 'jobs/:jobId', canActivate: hr, data: { group: 'Recruitment', title: 'Candidates' },
        loadComponent: () => import('../../features/recruitment/job-candidates/job-candidates.component').then(m => m.JobCandidatesComponent) },
      { path: 'applicants', canActivate: hr, data: { group: 'Recruitment', title: 'Applicants' },
        loadComponent: () => import('../../features/recruitment/applicants/applicants.component').then(m => m.ApplicantsComponent) },
      { path: 'applicants/new', canActivate: hr, data: { group: 'Recruitment', title: 'New application' },
        loadComponent: () => import('../../features/recruitment/job-application-form/job-application-form.component').then(m => m.JobApplicationFormComponent) },
      { path: 'applicant/:id', canActivate: hr, data: { group: 'Recruitment', title: 'Applicant' },
        loadComponent: () => import('../../features/recruitment/applicant-detail/applicant-detail.component').then(m => m.ApplicantDetailComponent) },
      { path: 'applicant/:applicantId/hire', canActivate: hr, data: { group: 'Recruitment', title: 'Hire' },
        loadComponent: () => import('../../features/recruitment/hire-employee/hire-employee.component').then(m => m.HireEmployeeComponent) },
      { path: 'cv-search', canActivate: hr, data: { group: 'Recruitment', title: 'CV search' },
        loadComponent: () => import('../../features/recruitment/cv-search/cv-search.component').then(m => m.CvSearchComponent) },

      // ---- AI
      { path: 'budget', canActivate: hr, data: { group: 'AI & strategy', title: 'Budget advisor' },
        loadComponent: () => import('../../features/ai/hr-budget-advisor/hr-budget-advisor.component').then(m => m.HrBudgetAdvisorComponent) },
      { path: 'retention', canActivate: hr, data: { group: 'AI & strategy', title: 'Retention strategy' },
        loadComponent: () => import('../../features/ai/hr-retention/hr-retention.component').then(m => m.HrRetentionComponent) },

      // ---- self-service
      { path: 'me', data: { group: 'Workspace', title: 'My space' },
        loadComponent: () => import('../../features/me/my-space.component').then(m => m.MySpaceComponent) },

      // ---- administration
      { path: 'admin/users', canActivate: admin, data: { group: 'Administration', title: 'Users & roles' },
        loadComponent: () => import('../../features/admin/users/admin-users.component').then(m => m.AdminUsersComponent) },
      { path: 'admin/users/new', canActivate: admin, data: { group: 'Administration', title: 'New account' },
        loadComponent: () => import('../../features/admin/new-user/new-user.component').then(m => m.NewUserComponent) },
      { path: 'admin/audit', canActivate: admin, data: { group: 'Administration', title: 'Audit log' },
        loadComponent: () => import('../../features/admin/audit/audit-log.component').then(m => m.AuditLogComponent) },
      { path: 'admin/models', canActivate: admin, data: { group: 'Administration', title: 'AI models' },
        loadComponent: () => import('../../features/admin/models/ai-models.component').then(m => m.AiModelsComponent) },

      { path: '**', redirectTo: '' }
    ]
  }
];
