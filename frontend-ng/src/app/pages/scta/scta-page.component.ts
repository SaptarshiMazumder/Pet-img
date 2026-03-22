import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-scta-page',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './scta-page.component.html',
  styleUrl: '../static-page.css',
})
export class SctaPageComponent {
  protected readonly lang = inject(LanguageService);
}
