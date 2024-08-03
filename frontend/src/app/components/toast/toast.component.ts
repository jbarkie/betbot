import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Toast, ToastService } from './toast.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="toast" class="toast toast-bottom toast-end">
      <div [ngClass]="{'alert-success': toast.type === 'success', 'alert-error': toast.type === 'error'}" class="alert">
        <span>{{ toast.message }}</span>
      </div>
    </div>
  `,
  styles: ``
})
export class ToastComponent {
  toast: Toast | null = null;
  private subscription: Subscription | undefined;

  constructor(private toastService: ToastService) {}

  ngOnInit() {
    this.subscription = this.toastService.toast$.subscribe(toast => {
      this.toast = toast;
      setTimeout(() => {
        this.toast = null;
      }, 3000);
    });
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
