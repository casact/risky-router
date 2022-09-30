<script lang="ts">
  import { onMount } from "svelte";

  const apiUrl = import.meta.env.VITE_API_URL;

  let time = "Waiting...";

  async function getTime() {
    const response = await fetch(apiUrl + "/time", {
      method: "GET",
    });
    const data = await response.json();

    time = data;
  }

  onMount(() => {
    getTime();
    const interval = setInterval(getTime, 15000);
    return () => clearInterval(interval);
  });
</script>

<div class="flex items-center justify-center">
  <ion-icon name="time-outline" />&nbsp;{time}
</div>
