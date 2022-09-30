<script lang="ts">
  import { onMount } from "svelte";

  const apiUrl = import.meta.env.VITE_API_URL;
  let chart_data = { x: [0], y: [0] };

  async function getFrequencyByHour() {
    const response = await fetch(apiUrl + "/frequency_by_hour", {
      method: "GET",
    });
    const data = await response.json();
    chart_data = data;
  }

  onMount(() => {
    getFrequencyByHour();
  });

  async function updateChart(data) {
    console.log(data);
    var frequencyChart = new Chart("frequencyHour", {
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
<center class="font-bold">Frequency of Accidents by Hour of Day</center>
  <canvas id="frequencyHour" style="width:100%;max-width:700px" />
</div>
