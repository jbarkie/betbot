import { Component } from '@angular/core';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [],
  template: `
    <div class="container mx-auto px-4 py-8">
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h1 class="card-title text-3xl mb-6">About BetBot</h1>

          <div class="space-y-6">
            <div>
              <h2 class="text-2xl font-semibold mb-3">Our Mission</h2>
              <p class="text-lg">
                BetBot is your intelligent companion for sports betting
                analytics. We combine cutting-edge technology with comprehensive
                sports data to provide you with informed betting insights.
              </p>
            </div>

            <div>
              <h2 class="text-2xl font-semibold mb-3">Features</h2>
              <ul class="list-disc list-inside space-y-2">
                <li>Real-time odds tracking across major sports leagues</li>
                <li>Advanced statistical analysis and predictions</li>
                <li>Personalized betting recommendations</li>
                <li>Historical performance data and trends</li>
              </ul>
            </div>
            
            <div>
              <h2 class="text-2xl font-semibold mb-3">Supported Sports</h2>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="card bg-base-200 p-4">
                  <div class="flex justify-between items-center">
                    <div>
                      <h3 class="font-bold">NBA</h3>
                      <p>National Basketball Association</p>
                    </div>
                    <img src="assets/img/logos/nba.png" alt="NBA logo" class="h-10 w-10 object-contain" />
                  </div>
                </div>
                <div class="card bg-base-200 p-4">
                  <div class="flex justify-between items-center">
                    <div>
                      <h3 class="font-bold">NFL</h3>
                      <p>National Football League</p>
                    </div>
                    <img src="assets/img/logos/nfl.png" alt="NFL logo" class="h-10 w-10 object-contain" />
                  </div>
                </div>
                <div class="card bg-base-200 p-4">
                  <div class="flex justify-between items-center">
                    <div>
                      <h3 class="font-bold">MLB</h3>
                      <p>Major League Baseball</p>
                    </div>
                    <img src="assets/img/logos/mlb.png" alt="MLB logo" class="h-10 w-10 object-contain" />
                  </div>
                </div>
                <div class="card bg-base-200 p-4">
                  <div class="flex justify-between items-center">
                    <div>
                      <h3 class="font-bold">NHL</h3>
                      <p>National Hockey League</p>
                    </div>
                    <img src="assets/img/logos/nhl.png" alt="NHL logo" class="h-10 w-10 object-contain" />
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  `,
  styles: ``,
})
export class AboutComponent {}
