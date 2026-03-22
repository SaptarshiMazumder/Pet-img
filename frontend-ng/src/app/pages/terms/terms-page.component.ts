import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-terms-page',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './terms-page.component.html',
  styleUrl: '../static-page.css',
})
export class TermsPageComponent {
  protected readonly lang = inject(LanguageService);
}
