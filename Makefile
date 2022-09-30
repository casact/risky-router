requirements:
	aptitude remove docker docker-engine docker.io containerd runc
	apt-get update
	apt-get install ca-certificates curl gnupg lsb-release
	mkdir -p /etc/apt/keyrings
	curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
	echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
	$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
	apt-get update
	apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin


osrm/washington-latest.osm.pbf:
	mkdir -p osrm
	wget http://download.geofabrik.de/north-america/us/washington-latest.osm.pbf
	mv washington-latest.osm.pbf osrm/washington-latest.osm.pbf

osrm/washington-latest.osrm.cell_metrics: osrm/washington-latest.osm.pbf
	docker run -t -v "${PWD}/osrm:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/washington-latest.osm.pbf
	docker run -t -v "${PWD}/osrm:/data" osrm/osrm-backend osrm-partition /data/washington-latest.osrm
	docker run -t -v "${PWD}/osrm:/data" osrm/osrm-backend osrm-customize /data/washington-latest.osrm

osrm: osrm/washington-latest.osrm.cell_metrics