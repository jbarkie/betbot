import { Component } from '@angular/core';
import { NavBarComponent } from '../nav-bar/nav-bar.component';

@Component({
    selector: 'app-page-header',
    imports: [NavBarComponent],
    template: `<header>
    <app-nav-bar />
  </header>`,
    styles: []
})
export class PageHeaderComponent {}
