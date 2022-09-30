<script lang="ts">
  import { onMount } from "svelte";

  const apiUrl = import.meta.env.VITE_API_URL;

  let weather = "Waiting...";

  async function getWeather() {
    const response = await fetch(apiUrl + "/weather", {
      method: "GET",
    });
    const data = await response.json();

    weather = data.charAt(0) + data.slice(1).toLowerCase();
  }

  onMount(() => {
    getWeather();
    const interval = setInterval(getWeather, 1000 * 60 * 15);
    return () => clearInterval(interval);
  });
</script>

<div class="flex items-center justify-center">
  {#if weather === "Clear"}
    <ion-icon name="sunny-outline" />
  {:else if weather === "Overcast"}
    <ion-icon name="cloudy-outline" />
  {:else if weather === "Rain"}
    <ion-icon name="rainy-outline" />
  {:else}
    <ion-icon name="rainy-outline" />
  {/if}
  &nbsp;{weather}
</div>
