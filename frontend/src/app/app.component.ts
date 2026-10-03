import { Component, inject } from '@angular/core';
import { NavigationError, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

const RELOADED_KEY = 'nexus_reloaded_for_new_version';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />'
})
export class AppComponent {
  constructor() {
    // After a new version is deployed, a page left open still points to the old
    // build's files, so opening a menu fails: reload once on the new version.
    inject(Router).events.pipe(filter((e): e is NavigationError => e instanceof NavigationError)).subscribe(e => {
      const message = String(e.error?.message ?? e.error ?? '');
      if (!/dynamically imported module|Importing a module script failed|Loading chunk/i.test(message)) return;
      try {
        if (sessionStorage.getItem(RELOADED_KEY)) return;     // only once, never a reload loop
        sessionStorage.setItem(RELOADED_KEY, '1');
      } catch { /* storage blocked: reload anyway */ }
      window.location.assign(e.url);
    });
    // a successful start on the current version allows the next automatic reload
    setTimeout(() => { try { sessionStorage.removeItem(RELOADED_KEY); } catch { /* ignore */ } }, 10000);
  }
}
