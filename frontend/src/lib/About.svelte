<script>
  import Link from "./Link.svelte";
  import RiskyRouterName from "./RiskyRouterName.svelte";
</script>

<div class="ml-12 my-8 mr-10 border-b-2 border-gray-300" />
<div
  class="grid grid-cols-12 gap-4 bg-blue-50 shadow-2xl rounded-lg ml-2 mt-4 p-5 text-lg"
>
  <div class="col-span-1" />
  <div class="col-span-10 px-8 mt-5">
    <h3 class="text-3xl font-mono font-semibold mb-4" id="about">
      About RiskyRouter
    </h3>
    <p>
      <RiskyRouterName /> is a route mapping software that provides an estimate of
      the accident risk of a chosen route and the risk of serious injury or fatality
      should an accident occur under certain conditions within the city of Seattle.
      <RiskyRouterName /> was created by <Link
        href={"#"}
        text={"Caesar Balona"}
      /> for the
      <Link
        href={"https://www.casact.org/article/reminder-apply-2022-cas-hacktuary-challenge?utm_source=pocket_mylist"}
        text={"2022 Casualty Actuarial Society Hacktuary Challenge"}
      />.
    </p>
    <br />
    <p>
      All the work is available open-source under the MPL-2.0 license as per the
      competition guidelines. My hope for the project is that it is a
      demonstration of what actuaries with access to the necessary skills can do
      not only for insurers but also for the public. It is not necessary for one
      individual actuary to have all the skills required, as individual skills
      can be found in several individuals and their efforts combined. An actuary
      with only actuarial skills will at least know what is possible and what
      skills to seek out. Further, I hope it serves as a resource for actuaries,
      data scientists, software developers, and web developers to use when
      building similar applications.
    </p>

    <br />

    <h3 class="font-semibold font-mono text-xl text-yale-blue">
      How <RiskyRouterName /> Works
    </h3>
    <p>
      <RiskyRouterName /> is made up of 4 components:
    </p>
    <ol class="list-decimal pl-12">
      <li>
        Frequency and severity models based on traffic and accident data from
        the city of Seattle, as well as additional accident data from the USA.
      </li>
      <li>A route mapping engine.</li>
      <li>A backend API to facilitate queries to the underlying models.</li>
      <li>A frontend web interface.</li>
    </ol>

    <br />

    <h4 class="font-semibold font-mono text-xl text-yale-blue">
      1. Frequency and Severity Models
    </h4>
    <p>
      Several models have been built to determine the frequency of accidents
      based on their geographic locations, and one model has been built to
      calculate the probability of serious injury or death in the event of an
      accident given several conditions.
    </p>
    <br />
    <h4 class="font-semibold font-mono text-yale-blue">Frequency Modelling</h4>

    <p>
      Data were collected from <Link
        href={"https://data.seattle.gov/"}
        text={"Seattle Open Data"}
      /> which provides open access data for the city of Seattle including GIS data.
      The data collected are:
    </p>
    <br />
    <table class="border-collapse border border-slate-500">
      <thead>
        <tr>
          <th class="border border-slate-400 p-1 font-bold">Data</th>
          <th class="border border-slate-400 p-1 font-bold">Detail</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="border border-slate-400 p-1"
            ><Link
              href={"https://data.seattle.gov/Transportation/Traffic-Flow-Map-Volumes/38vd-gytv"}
              text={"Traffic flow volume"}
            /></td
          >
          <td class="border border-slate-400 p-1"
            >Traffic volume in 5 minute intervals from select locations around
            Seattle.</td
          >
        </tr>
        <tr>
          <td class="border border-slate-400 p-1"
            ><Link
              href={"https://data-seattlecitygis.opendata.arcgis.com/datasets/SeattleCityGIS::seattle-streets/about"}
              text={"Detailed street data"}
            /></td
          >
          <td class="border border-slate-400 p-1"
            >Streets data includes Arterial Classification, Street Names, Block
            Number, Direction, One-way, Surface Width, Surface Type, Pavement
            Condition, Speed Limit, Percent Slope. The street data was primarily
            used to determine if a given coordinate is a street or intersection.</td
          >
        </tr>
        <tr>
          <td class="border border-slate-400 p-1"
            ><Link
              href={"https://data.seattle.gov/dataset/SDOT-Collisions-All-Years/9jdj-3h57"}
              text={"Collisions"}
            /></td
          >
          <td class="border border-slate-400 p-1"
            >Detail on traffic collisions in the city of Seattle including
            geographic coordinate.</td
          >
        </tr>
      </tbody>
    </table>

    <br />

    <p class="pb-3">
      In addition, historic weather data was collected from OpenMeteo and
      included in the volume data to determine weather at the time of traffic
      volume recording.
    </p>

    <p class="pb-3">
      The data are downloaded programmatically from the Seattle Open Data
      website. Thereafter they are transformed into the format needed for the
      modelling.
    </p>

    <p class="pb-3">
      Traffic volume data is collected at certain predetermined locations around
      Seattle, and hence volume is not known for all possible streets and
      routes. K-Nearest Neighbours was used to classify street point coordinates
      to their nearest traffic volume recording station. This way, every segment
      on every street (including intersections) will have an associated traffic
      volume at a given time, on a given day, under certain weather conditions.
      This traffic volume is used as the exposure metric in the frequency model.
    </p>

    <p class="pb-3">
      Collision data maps directly to street coordinate data, and hence
      collision data can easily be joined with volume data by coordinate, date
      and time. This creates the final dataset used to build a frequency model.
    </p>

    <p class="pb-3">
      For the full underlying code of how the frequency data is built, refer to
      model/src/data/seattle.
    </p>

    <p class="pb-3">
      Fitting a single frequency model to all the data is not ideal, as this
      will result in heterogenous variance as it is not expected that the
      frequency distribution is the same at all stations. Instead, a separate
      frequency model is fit for each station where volume is recorded. This is
      beneficial, as it is expected areas in the central business district will
      exhibit different frequency behaviour to suburban areas. Hence, the model
      first uses a decision tree to select the appropriate model to use given
      proximity to a traffic volume station, and then predicts frequency using
      that model. This means that a chosen route may use several different
      frequency prediction models.
    </p>

    <p class="pb-3">
      For each model, a gradient boosting machine (GBM) is used to predict
      frequency. Several models were assessed, from basic GLMs, to random
      forest, and even nearest-neighbour-based approaches. However, the GBM
      performed the best overall, and handled the imbalance inherent in the data
      most appropriately. (Note there is significant imbalance as data is
      hourly, and in most cases, 97-98% of the data has no recorded collisions).
    </p>

    <p class="pb-3">
      Details on the model can be found in model/src/models/frequency.py
    </p>

    <h4 class="font-semibold font-mono text-yale-blue">Severity Modelling</h4>
    <p>
      Separate data is used for severity modelling, as the collision data
      provided by Seattle has limited features on which to predict. Collision
      data was collected from the National Highway Traffic Safety Administration
      Crash Report Sampling System. The data are transformed for modelling. This
      detail can be found in model/src/data/crss. The objective is to predict
      whether an accident results in serious injury or death. Again, several
      models were assessed, with the best performing being a balanced random
      forest, due to the imbalance in the data, where most accidents result in
      minor injury or no injury. Details on the model can be found in
      model/src/models/severity.py
    </p>
    <br />
    <h4 class="font-semibold font-mono text-xl text-yale-blue">
      The Route Mapping Engine
    </h4>
    <p>
      The route mapping engine used is OSRM and is limited to the state of
      Washington. OSRM is a C++ implementation of a high-performance routing
      engine to find the shortest paths in a road network. The elements of the
      route are passed to the frequency model to determine frequency of
      accidents along a route and are adjusted to the time travelled (as the
      exposure data is per hour).
    </p>
    <br />
    <h4 class="font-semibold font-mono text-xl text-yale-blue">Backend API</h4>
    <p class="pb-3">
      The backend API is the link between the models and the webpage and routing
      module. The backend API feeds the routing and webpage data to the
      appropriate model, as well as fetches the current time and weather
      conditions in Seattle.
    </p>
    <p class="pb-3">
      The backend is built using FastAPI, an open-source python package for
      fast, scalable APIs.
    </p>
    <p>
      The existence of an API also allows programmatic access to the models. For
      example, an insurer can bulk query the API using policy information to
      determine the riskiness of routes travelled by policyholders. Or, an
      insurer can query the API using their existing rating software at quote
      state to determine a premium, without needing to access the frontend web
      interface.
    </p>
    <br />
    <h4 class="font-semibold font-mono text-xl text-yale-blue">
      Frontend Web Interface
    </h4>
    <p class="pb-3">
      The frontend web interface is what the end-user interacts with and
      surfaces all the previous components in one easy to use location.
    </p>
    <p class="pb-3">
      The top bar directly below the title gives the current weather, weekday,
      and time in Seattle. The middle left block houses the routing interface
      where routes can be found similar to google maps. The middle right
      provides the frequency and severity of a given route, and allows the user
      to change additional items such as age, car, and speed. The bottom
      provides some additional information to advise on safer options.
    </p>
    <p class="pb-3">
      The frontend is built using Javascript and hosted on a server at
      riskyrouter.com. The deployment is performed using Docker. For the actual
      website, I have served it using nginx and provided secured certificates.
      Anyone can clone the github repository and host the website on their own
      server in exactly the same manner, needing only to provide their own
      domain name, server, and server configuration. Docker removes all the
      admin of deployment except for these final parts which are unique to every
      deployment. Individual items can be deployed separately. For example, an
      insurer can deploy only the API and routing module within their company to
      query the API locally.
    </p>
    <br />

    <h4 class="font-semibold font-mono text-xl text-yale-blue">Use Cases</h4>
    <p><RiskyRouterName /> has many uses cases for different users.</p>
    <br />
    <table class="border-collapse border border-slate-500">
      <thead>
        <tr>
          <td class="border border-slate-400 p-1 font-bold">User</td>
          <td class="border border-slate-400 p-1 font-bold">Use Case</td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="border border-slate-400 p-1 font-bold"
            >General public in Seattle</td
          >
          <td class="border border-slate-400 p-1"
            >Understanding the riskiness of their commute or any travel they may
            undertake within Seattle and opt to alter travel arrangements to
            reduce risk.</td
          >
        </tr>
        <tr>
          <td class="border border-slate-400 p-1 font-bold">General public</td>
          <td class="border border-slate-400 p-1"
            >Understand the risk of serious injury or death in the event of an
            accident based on certain conditions such as weather, time of day,
            speed, age, vehicle year, and whether they have been drinking.</td
          >
        </tr>
        <tr>
          <td class="border border-slate-400 p-1 font-bold">Governments</td>
          <td class="border border-slate-400 p-1"
            >Educate the public on the dangers of drunk driving or speeding, and
            importance of having safer and more recent vehicles. Focused
            initiatives to reduce accident frequency on hotspot routes.
          </td>
        </tr>
        <tr>
          <td class="border border-slate-400 p-1 font-bold"
            >Personal auto insurers</td
          >
          <td class="border border-slate-400 p-1"
            >Determine the accident frequency of existing or potential
            policyholders based on their frequent commutes and use this to offer
            discounts, determine premiums, or alter behaviour to reduce risk.
            This may be a more palatable option than full in-vehicle telematics.
            For example, two individuals may have exactly the same
            characteristics, but one may have a much lower risk travel profile
            than the other, and should then be attracted as a risk with a lower
            premium.</td
          >
        </tr>
        <tr>
          <td class="border border-slate-400 p-1 font-bold"
            >Health and life insurers</td
          >
          <td class="border border-slate-400 p-1"
            >Understand the serious injury and fatality risk of policyholders
            based on their frequent commutes.</td
          >
        </tr>
      </tbody>
    </table>

    <br />

    <h4 class="font-semibold font-mono text-xl text-yale-blue">Limitations</h4>
    <p>
      Being based on statistical models, <RiskyRouterName /> obviously has several limitations:
    </p>
    <ul class="list-disc pl-12">
      <li>
        Class imbalance was a major problem in the modelling, and all results
        should be interpreted with this in mind.
      </li>
      <li>
        As models are only estimates of reality, they should not be taken as
        absolute truth, but only indications of relationships found within the
        data.
      </li>
      <li>
        I do not recommend RiskyRouter be used for for anything more than
        interest sake or demonstration. To use it for actual production purposes
        would require significant additional development as well as peer review
        and sign off by appropriately qualified individuals (such as a statutory
        actuary).
      </li>
    </ul>
  </div>
  <div class="col-span-1" />
</div>
