<script lang="ts">
  import { onMount } from "svelte";

  const apiUrl = import.meta.env.VITE_API_URL;
  let chart_data = { x: [0], y: [0] };

  async function getFrequencyByWeather() {
    const response = await fetch(apiUrl + "/frequency_by_weather", {
      method: "GET",
    });
    const data = await response.json();
    chart_data = data;
  }

  onMount(() => {
    getFrequencyByWeather();
  });

  async function updateChart(data) {
    console.log(data);
    var frequencyChart = new Chart("frequencyWeather", {
      type: "bar",
      data: {
        labels: data.x,
        datasets: [
          {
            data: data.y,
            label: "Frequency",
            backgroundColor: "#247BA0",
          },
        ],
      },
    });
  }

  $: chart_data, updateChart(chart_data);
</script>

<div>
  <center class="font-bold">Frequency of Accidents by Weather</center>
  <canvas id="frequencyWeather" style="width:100%;max-width:700px" />
</div>
