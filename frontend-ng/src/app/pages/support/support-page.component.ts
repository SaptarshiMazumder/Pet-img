import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-support-page',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './support-page.component.html',
  styleUrl: '../static-page.css',
})
export class SupportPageComponent {
  protected readonly lang = inject(LanguageService);
}
