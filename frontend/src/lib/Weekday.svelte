<script lang="ts">
  import { onMount } from "svelte";

  const apiUrl = import.meta.env.VITE_API_URL;

  let weekday = "Waiting...";

  async function getWeekday() {
    const response = await fetch(apiUrl + "/weekday", {
      method: "GET",
    });
    const data = await response.json();

    weekday = data.charAt(0) + data.slice(1).toLowerCase();
  }

  onMount(() => {
    getWeekday();
    const interval = setInterval(getWeekday, 60000);
    return () => clearInterval(interval);
  });
</script>

<div class="flex items-center justify-center">
  <ion-icon name="calendar-clear-outline" />&nbsp;{weekday}
</div>
