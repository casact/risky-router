<script lang="ts">
  import { onMount } from "svelte";
  import About from "./lib/About.svelte";
  import HourFrequency from "./lib/HourFrequency.svelte";
  import WeatherFrequency from "./lib/WeatherFrequency.svelte";
  import Leaflet from "./lib/Leaflet.svelte";
  import Time from "./lib/Time.svelte";
  import Weather from "./lib/Weather.svelte";
  import Weekday from "./lib/Weekday.svelte";

  const apiUrl = import.meta.env.VITE_API_URL;

  let injury_fatal_prob = 0;

  let formatted_injury_fatal_prob = "...";

  let body_type = 1;
  let vehicle_year = "2010_TO_CURRENT";
  let relative_speed = 0.9;
  let alcohol = false;

  let injury_fatal_prob_alcohol_delta = 0;
  let injury_fatal_prob_speeding_delta = 0;

  let formatted_injury_fatal_prob_alcohol_delta = "...";
  let formatted_injury_fatal_prob_speeding_delta = "...";

  let user = {
    body_type: body_type,
    vehicle_year: vehicle_year,
    relative_speed: relative_speed,
    alcohol: alcohol,
  };

  let body_type_options = [
    { value: 1, text: "Car" },
    { value: 0, text: "Motorbike" },
  ];

  let limit_base = 0.9;
  let speeding_base = 1.2;
  let excessive_base = 2.0;
  let relative_speed_options = [
    { value: limit_base, text: "Within the limit" },
    { value: speeding_base, text: "Speeding" },
    { value: excessive_base, text: "Excessive" },
  ];

  let vehicle_year_options = [
    { value: "PRE_2000", text: "<2000" },
    { value: "2000_TO_2010", text: "2000 - 2010" },
    { value: "2010_TO_CURRENT", text: "2010+" },
  ];

  async function getSeverity(user) {
    formatted_injury_fatal_prob = "...";

    const response = await fetch(
      apiUrl +
        "/severity?" +
        new URLSearchParams({
          body_type: user.body_type,
          vehicle_year: user.vehicle_year,
          relative_speed: user.relative_speed,
          alcohol: user.alcohol,
        }),
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      }
    );
    const data = await response.json();

    injury_fatal_prob = data.injury_fatal_prob;

    if (injury_fatal_prob >= 0.01) {
      formatted_injury_fatal_prob = new Intl.NumberFormat("en-US", {
        style: "percent",
      }).format(injury_fatal_prob);
    } else {
      formatted_injury_fatal_prob = "< 1%";
    }
  }

  async function getSeverityAlcoholSwitch(user) {
    formatted_injury_fatal_prob_alcohol_delta = "...";
    let negate_alcohol: string;

    if (alcohol) {
      negate_alcohol = "false";
    } else {
      negate_alcohol = "true";
    }

    const response = await fetch(
      apiUrl +
        "/severity?" +
        new URLSearchParams({
          body_type: user.body_type,
          vehicle_year: user.vehicle_year,
          relative_speed: user.relative_speed,
          alcohol: negate_alcohol,
        }),
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      }
    );
    const data = await response.json();

    console.log(injury_fatal_prob);
    console.log(data.injury_fatal_prob);

    injury_fatal_prob_alcohol_delta =
      injury_fatal_prob - data.injury_fatal_prob;
    formatted_injury_fatal_prob_alcohol_delta = new Intl.NumberFormat("en-US", {
      style: "percent",
    }).format(Math.abs(injury_fatal_prob_alcohol_delta));
  }

  async function getSeveritySpeedingSwitch(user) {
    let speed_switcher;
    if (user.relative_speed > speeding_base) {
      speed_switcher = limit_base;
    } else if (user.relative_speed > limit_base) {
      speed_switcher = limit_base;
    } else {
      speed_switcher = excessive_base;
    }

    const response = await fetch(
      apiUrl +
        "/severity?" +
        new URLSearchParams({
          body_type: user.body_type,
          age_of_driver: user.age_of_driver,
          vehicle_year: user.vehicle_year,
          relative_speed: speed_switcher,
          alcohol: user.alcohol,
          distraction: user.distraction,
        }),
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      }
    );

    const data = await response.json();

    injury_fatal_prob_speeding_delta =
      injury_fatal_prob - data.injury_fatal_prob;
    formatted_injury_fatal_prob_speeding_delta = new Intl.NumberFormat(
      "en-US",
      {
        style: "percent",
      }
    ).format(Math.abs(injury_fatal_prob_speeding_delta));
  }

  $: injury_fatal_prob, getSeverityAlcoholSwitch(user);
  $: injury_fatal_prob, getSeveritySpeedingSwitch(user);

  onMount(() => {
    getSeverity(user);
  });

  const onBodyTypeChange = () => {
    body_type = user.body_type;
    getSeverity(user);
  };

  const onVehicleYearChange = () => {
    vehicle_year = user.vehicle_year;
    getSeverity(user);
  };

  const onRelativeSpeedChange = () => {
    relative_speed = user.relative_speed;
    getSeverity(user);
  };

  const onAlcoholChange = () => {
    alcohol = user.alcohol;
    getSeverity(user);
  };
</script>

<Leaflet />

<main>
  <div class="container mx-auto pb-20">
    <div
      class="flex mt-2 ml-2 mb-0 p-3 pl-4 bg-space-cadet rounded-t-lg text-white items-center font-mono tracking-wide"
    >
      <h3 class="flex-none w-32 text-3xl font-bold">RiskyRouter</h3>
      <div class="grow" />
      <div class="flex-none w-32 text-center text-lg">
        <a href="#about" class="text hover:font-bold">About</a>
      </div>
    </div>
    <div class="grid grid-cols-12">
      <div
        class="col-span-12 grid grid-cols-12 text-center bg-slate-300 shadow-2xl rounded-b-lg ml-2 mb-2 p-2"
      >
        <div class="col-span-4 text-lg font-semibold"><Weather /></div>
        <div class="col-span-4 text-lg font-semibold"><Weekday /></div>
        <div class="col-span-4 text-lg font-semibold"><Time /></div>
      </div>
      <div id="map" class="map col-span-7 mx-2 shadow-xl rounded-lg" />
      <div class="col-span-5 bg-slate-50 shadow-2xl rounded-lg p-5">
        <div class="grid grid-cols-12 gap-4">
          <div class="col-span-12 pb-1 italic text-lg text-gray-600">
            Based on the weather, week day, and time of day...
          </div>
          <!-- Frequency -->
          <div class="col-span-2 text-center flex items-center justify-center">
            <ion-icon
              class="text-space-cadet"
              name="pulse-outline"
              size="large"
            />
          </div>
          <div class="col-span-10 text-lg font-semibold">
            At least
            <span class="text-yale-blue text-xl font-extrabold text-right"
              >1</span
            >
            vehicle involved in an accident on this route for every
            <span
              class="text-yale-blue text-xl font-extrabold text-right"
              id="per_x_vehicles">...</span
            >
            vehicles
          </div>
          <div class="col-span-2 text-center flex items-center justify-center">
            <ion-icon
              class="text-space-cadet"
              name="time-outline"
              size="large"
            />
          </div>
          <div class="col-span-10 text-lg font-semibold">
            An accident occurs every
            <span
              class="text-yale-blue text-xl font-extrabold text-right"
              id="return_period">...</span
            >
            to
            <span
              class="text-yale-blue text-xl font-extrabold text-right"
              id="return_period_plus_1">...</span
            >
            days on routes similar to this based on its median daily traffic volume
          </div>

          <div class="col-span-12 py-1 italic text-lg text-gray-600">
            If you happen to be in an accident...
          </div>

          <!-- Severity -->
          <div class="col-span-2 text-center flex items-center justify-center">
            <ion-icon
              class="text-space-cadet"
              name="bandage-outline"
              size="large"
            />
          </div>
          <div class="col-span-10 text-lg font-semibold">
            It may result in serious injury or fatality with at least
            <span
              class="text-yale-blue text-xl font-extrabold text-right"
              id="injury_fatal_prob">{formatted_injury_fatal_prob}</span
            >
            probability.
          </div>
        </div>
        <div class="grid grid-cols-12 gap-4 mt-6">
          <div class="col-span-3 text-cg-blue font-bold p-1">Vehicle Year</div>
          <select
            class="col-span-3 border-2 rounded-md p-1 border-cg-blue"
            bind:value={user.vehicle_year}
            on:change={onVehicleYearChange}
          >
            {#each vehicle_year_options as option}
              <option
                value={option.value}
                selected={vehicle_year === option.value}>{option.text}</option
              >
            {/each}
          </select>
          <div class="col-span-3 text-cg-blue font-bold p-1">Car</div>
          <select
            class="col-span-3 border-2 rounded-md p-1 border-cg-blue"
            bind:value={user.body_type}
            on:change={onBodyTypeChange}
          >
            {#each body_type_options as option}
              <option value={option.value} selected={body_type === option.value}
                >{option.text}</option
              >
            {/each}
          </select>
          <div class="col-span-3 text-cg-blue font-bold p-1">
            Relative Speed
          </div>
          <select
            class="col-span-3 border-2 rounded-md p-1 border-cg-blue"
            bind:value={user.relative_speed}
            on:change={onRelativeSpeedChange}
          >
            {#each relative_speed_options as option}
              <option
                value={option.value}
                selected={relative_speed === option.value}>{option.text}</option
              >
            {/each}
          </select>
          <div class="col-span-3 text-cg-blue font-bold p-1">Drinking?</div>
          <input
            class="col-span-3 border-2 rounded-md p-1 border-cg-blue disabled:cursor-not-allowed"
            type="checkbox"
            bind:checked={user.alcohol}
            on:change={onAlcoholChange}
          />
        </div>
        <div class="mt-8 px-3 mx-10 text-red-salsa">
          <center
            ><ion-icon name="warning-outline" class="text-2xl" />
            <p class="text-sm">
              The values given above are based on limited data and approximate
              models and should not be used to justify risky behaviour. In some
              rare cases, probabilities will be inconsistent. It is irrefutable
              that <span
                data-text="Researchers from the Insurance Institute for Highway Safety (IIHS) found that a 5 mph increase in the maximum speed limit was associated with an 8% increase in the fatality rate on interstates and freeways, and a 3% increase in fatalities on other roads."
                class="tooltip left"
                ><a
                  class="underline font-bold"
                  href="https://nacto.org/publication/city-limits/the-need/speed-kills/"
                  >increased speed kills</a
                ></span
              >
              and that
              <span
                data-text="The risk of a driver under the influence of alcohol being killed in a vehicle accident is at least eleven times that of drivers without alcohol in their system. "
                class="tooltip left"
                ><a
                  class="underline font-bold"
                  href="https://www.notodrugs.co.za/drugfacts/alcohol/drinking-and-driving.html"
                  >drinking and driving kills</a
                ></span
              > and is illegal.
            </p></center
          >
        </div>
      </div>
      <div
        class="col-span-12 grid grid-cols-12 text-center items-center bg-blue-50 shadow-2xl rounded-t-lg ml-2 mt-3 py-4 pt-6 px-2"
      >
        <div class="col-span-1 text-lg font-semibold" />
        <div class="col-span-4 text-lg font-semibold">
          {#if user.relative_speed > speeding_base}
            <div class="flex  items-center justify-center">
              <div class="flex-none w-16">
                <ion-icon
                  name="alert-circle-outline"
                  size="large"
                  class="text-red-salsa"
                />
              </div>
              <div class="text-lg font-semibold">
                {#if injury_fatal_prob_speeding_delta > 0.01}
                  Excessive speeding increases the risk of serious injury or
                  fatality by <span
                    class="text-yale-blue text-xl font-extrabold text-right"
                    >{formatted_injury_fatal_prob_speeding_delta}</span
                  >! Take it easy and stick to the recommended speed limits.
                {:else}
                  Excessive speeding increases the risk of an accident! Take it
                  easy and stick to the recommended speed limits.
                {/if}
              </div>
            </div>
          {:else if user.relative_speed > limit_base}
            <div class="flex items-center justify-center">
              <div class="flex-none w-16">
                <ion-icon
                  name="speedometer-outline"
                  size="large"
                  class="text-red-salsa"
                />
              </div>
              <div class="text-lg font-semibold">
                {#if injury_fatal_prob_speeding_delta > 0.01}
                  Speeding increases the risk of serious injury or fatality by <span
                    class="text-yale-blue text-xl font-extrabold text-right"
                    >{formatted_injury_fatal_prob_speeding_delta}</span
                  >! Take it easy and stick to the recommended speed limits.
                {:else}
                  Speeding increases the risk of an accident! Take it easy and
                  stick to the recommended speed limits.
                {/if}
              </div>
            </div>
          {:else}
            <div class="flex  items-center justify-center">
              <div class="flex-none w-16">
                <ion-icon
                  name="speedometer-outline"
                  size="large"
                  class="text-green-500"
                />
              </div>
              <div class="text-lg font-semibold">
                {#if injury_fatal_prob_speeding_delta < -0.01}
                  Good job on sticking to the speed limit! Excessive speeding
                  increases the risk of serious injury or fatality by <span
                    class="text-yale-blue text-xl font-extrabold text-right"
                    >{formatted_injury_fatal_prob_speeding_delta}</span
                  >.
                {:else}
                  Good job on sticking to the speed limit! Excessive speeding
                  increases the risk of an accident.
                {/if}
              </div>
            </div>
          {/if}
        </div>
        <div class="col-span-2 text-lg font-semibold" />
        <div class="col-span-4 text-lg font-semibold">
          {#if user.alcohol}
            <div class="flex  items-center justify-center">
              <div class="flex-none w-16">
                <ion-icon
                  name="sad-outline"
                  size="large"
                  class="text-red-salsa"
                />
              </div>
              <div class="text-lg font-semibold">
                {#if injury_fatal_prob_alcohol_delta > 0.01}
                  Never drink and drive. Using a designated driver will reduce
                  serious injury or fatality risk in the event of an accident by <span
                    class="text-yale-blue text-xl font-extrabold text-right"
                    >{formatted_injury_fatal_prob_alcohol_delta}</span
                  >.
                {:else}
                  Never drink and drive. Using a designated driver will reduce
                  the risk of an accident.
                {/if}
              </div>
            </div>
          {:else}
            <div class="flex items-center justify-center">
              <div class="flex-none w-16">
                <ion-icon
                  name="happy-outline"
                  size="large"
                  class="text-green-500"
                />
              </div>
              <div class="text-lg font-semibold">
                {#if injury_fatal_prob_alcohol_delta < -0.01}
                  Good job on staying sober or having a designated driver!
                  Driving under the influence increases serious injury or
                  fatality risk by <span
                    class="text-yale-blue text-xl font-extrabold text-right"
                    id="injury_fatal_prob"
                    >{formatted_injury_fatal_prob_alcohol_delta}</span
                  >.
                {:else}
                  Good job on staying sober or having a designated driver! Using
                  a designated driver will reduce the risk of an accident.
                {/if}
              </div>
            </div>
          {/if}
        </div>
        <div class="col-span-1 text-lg font-semibold" />
      </div>
      <div
        class="col-span-12 grid grid-cols-12 text-center items-center bg-blue-50 ml-2 p-2"
      >
        <div class="col-span-1" />
        <div class="col-span-10 border-b-2" />
        <div class="col-span-1" />
      </div>
      <div
        class="col-span-12 grid grid-cols-12 text-center items-center bg-blue-50 shadow-2xl ml-2 py-4 pb-8 px-8 rounded-b-md"
      >
        <div class="col-span-6"><HourFrequency /></div>
        <div class="col-span-6"><WeatherFrequency /></div>
      </div>
    </div>
    <About />
  </div>
</main>

<style>
</style>
