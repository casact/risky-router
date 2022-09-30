# About RiskyRouter

`RiskyRouter` is a route mapping software that provides an estimate of the accident risk of a chosen route and the risk of serious injury or fatality should an accident occur under certain conditions within the city of Seattle. `RiskyRouter` was created by Caesar Balona for the 2022 Casualty Actuarial Society Hacktuary Challenge.

All the work is available open-source under the MPL-2.0 license as per the competition guidelines. My hope for the project is that it is a demonstration of what actuaries with access to the necessary skills can do not only for insurers but also for the public. It is not necessary for one individual actuary to have all the skills required, as individual skills can be found in several individuals and their efforts combined. An actuary with only actuarial skills will at least know what is possible and what skills to seek out. Further, I hope it serves as a resource for actuaries, data scientists, software developers, and web developers to use when building similar applications.

## How `RiskyRouter` Works

`RiskyRouter` is made up of 4 components:

1. Frequency and severity models based on traffic and accident data from the city of Seattle, as well additional accident data from the USA.
1. A route mapping engine.
1. A backend API to facilitate queries to the underlying models.
1. A frontend web interface.


## Frequency and Severity Models

Several models have been built to determine the frequency of accidents based on their geographic locations, and one model has been built to calculate the probability of serious injury or death in the event of an accident given several conditions.

### Frequency Modelling

Data were collected from [Seattle Open Data](https://data.seattle.gov/) which provides open access data for the city of Seattle including GIS data. The data collected are:

| Data | Detail |
| ---- | ------ |
| Traffic flow volume | Traffic volume in 5 minute intervals from select locations around Seattle. |
| Detailed street data | Streets data includes Arterial Classification, Street Names, Block Number, Direction, One-way, Surface Width, Surface Type, Pavement Condition, Speed Limit, Percent Slope. The street data was primarily used to determine if a given coordinate is a street or intersection. |
| Collisions | Detail on traffic collisions in the city of Seattle including geographic coordinate.|

In addition, historic weather data was collected from OpenMeteo and included in the volume data to determine weather at the time of traffic volume recording.

The data are downloaded programmatically from the Seattle Open Data website. Thereafter they are transformed into the format needed for the modelling.

Traffic volume data is collected at certain predetermined locations around Seattle, and hence volume is not known for all possible streets and routes. K-Nearest Neighbours was used to classify street point coordinates to their nearest traffic volume recording station. This way, every segment on every street (including intersections) will have an associated traffic volume at a given time, on a given day, under certain weather conditions. This traffic volume is used as the exposure metric in the frequency model.

Collision data maps directly to street coordinate data, and hence collision data can easily be joined with volume data by coordinate, date and time. This creates the final dataset used to build a frequency model.

For the full underlying code of how the frequency data is built, refer to model/src/data/seattle.

Fitting a single frequency model to all the data is not ideal, as this will result in heterogenous variance as it is not expected that the frequency distribution is the same at all stations. Instead, a separate frequency model is fit for each station where volume is recorded. This is beneficial, as it is expected areas in the central business district will exhibit different frequency behaviour to suburban areas. Hence, the model first uses a decision tree to select the appropriate model to use given proximity to a traffic volume station, and then predicts frequency using that model. This means that a chosen route may use several different frequency prediction models.

For each model, a gradient boosting machine (GBM) is used to predict frequency. Several models were assessed, from basic GLMs, to random forest, and even nearest-neighbour-based approaches. However, the GBM performed the best overall, and handled the imbalance inherent in the data most appropriately. (Note there is significant imbalance as data is hourly, and in most cases, 97-98% of the data has no recorded collisions).

Details on the model can be found in model/src/models/frequency.py

### Severity Modelling

Separate data is used for severity modelling, as the collision data provided by Seattle has limited features on which to predict. Collision data was collected from the National Highway Traffic Safety Administration Crash Report Sampling System. The data are transformed for modelling. This detail can be found in model/src/data/crss. The objective is to predict whether an accident results in serious injury or death. Again, several models were assessed, with the best performing being a balanced random forest, due to the imbalance in the data, where most accidents result in minor injury or no injury. Details on the model can be found in model/src/models/severity.py

## The Route Mapping Engine

The route mapping engine used is OSRM and is limited to the state of Washington. OSRM is a C++ implementation of a high-performance routing engine to find the shortest paths in a road network. The elements of the route are passed to the frequency model to determine frequency of accidents along a route and are adjusted to the time travelled (as the exposure data is per hour).

## Backend API

The backend API is the link between the models and the webpage and routing module. The backend API feeds the routing and webpage data to the appropriate model, as well as fetches the current time and weather conditions in Seattle.

The backend is built using FastAPI, an open-source python package for fast, scalable APIs.

The existence of an API also allows programmatic access to the models. For example, an insurer can bulk query the API using policy information to determine the riskiness of routes travelled by policyholders. Or, an insurer can query the API using their existing rating software at quote state to determine a premium, without needing to access the frontend web interface.

## Frontend Web Interface

The frontend web interface is what the end-user interacts with and surfaces all the previous components in one easy to use location.

The top bar directly below the title gives the current weather, weekday, and time in Seattle. The middle left block houses the routing interface where routes can be found similar to google maps. The middle right provides the frequency and severity of a given route, and allows the user to change additional items such as age, car, and speed. The bottom provides some additional information to advise on safer options.

The frontend is built using Javascript and hosted on a server at [RiskyRouter.com](https://riskyrouter.com/). The deployment is performed using Docker. For the actual website, I have served it using nginx and provided secured certificates. Anyone can clone the github repository and host the website on their own server in exactly the same manner, needing only to provide their own domain name, server, and server configuration. Docker removes all the admin of deployment except for these final parts which are unique to every deployment. Individual items can be deployed separately. For example, an insurer can deploy only the API and routing module within their company to query the API locally.

# Use Cases

`RiskyRouter` has many uses cases for different users.

| User | Use Case |
| ---- | -------- |
| General public in Seattle |	Understanding the riskiness of their commute or any travel they may undertake within Seattle and opt to alter travel arrangements to reduce risk. |
|General public | Understand the risk of serious injury or death in the event of an accident based on certain conditions such as weather, time of day, speed, age, vehicle year, and whether they have been drinking.
|Governments | Educate the public on the dangers of drunk driving or speeding, and importance of having safer and more recent vehicles. Focused initiatives to reduce accident frequency on hotspot routes.
|Personal auto insurers | Determine the accident frequency of existing or potential policyholders based on their frequent commutes and use this to offer discounts, determine premiums, or alter behaviour to reduce risk. This may be a more palatable option than full in-vehicle telematics. For example, two individuals may have exactly the same characteristics, but one may have a much lower risk travel profile than the other, and should then be attracted as a risk with a lower premium.|
| Health and life insurers | Understand the serious injury and fatality risk of policyholders based on their frequent commutes.|

# Limitations

Being based on statistical models, `RiskyRouter` obviously has several limitations:

* Class imbalance was a major problem in the modelling, and all results should be interpreted with this in mind.
* As models are only estimates of reality, they should not be taken as absolute truth, but only indications of relationships found within the data.
* I do not recommend `RiskyRouter` be used for for anything more than interest sake or demonstration. To use it for actual production purposes would require significant additional development as well as peer review and sign off by appropriately qualified individuals (such as a statutory actuary).

