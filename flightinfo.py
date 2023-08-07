import requests
import csv
import math
import time

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c
    distance_nm = distance_km * 0.539957  # Convert to nautical miles
    return distance_nm

def get_flight_status(flight_data, destination):
    vertical_speed = flight_data.get("Vsi")
    altitude = flight_data.get("Alt")
    ground_speed = flight_data.get("Spd")
    gnd = flight_data.get("Gnd")

    if vertical_speed is None or altitude is None:
        return "UNKNOWN"

    if destination == "Dubrovnik":
        if -300 <= vertical_speed <= 300:
            return "EN ROUTE"
        elif ground_speed == 0 and gnd:
            return "ARRIVED AT THE GATE"
        elif altitude >= 10000 and ground_speed > 0:
            return "ARRIVING"
        elif altitude < 10000 and altitude >= 4000 and ground_speed > 0:
            return "APPROACHING"
        elif altitude < 4000 and altitude >= 0 and ground_speed > 0:
            return "LANDING"
        elif altitude < 0 and ground_speed > 30:
            return "LANDED"
        elif altitude < 0 and ground_speed <= 30:
            return "MISSED APPROACH"
        elif ground_speed <= 30:
            return "TAXI TO THE GATE"
        elif ground_speed == 0 and gnd:
            return "ARRIVED AT THE GATE"

    elif destination != "Dubrovnik":
        if ground_speed <= 30:
            return "TAXI TO THE RUNWAY"
        elif vertical_speed >= 300:
            return "DEPARTING"
        elif -300 <= vertical_speed <= 300:
            return "CRUISING TO DESTINATION"

def read_routes_data(file_path):
    routes_data = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            if len(row) != 2:
                continue  # Skip rows with incorrect format
            callsign, route = row
            route = route.strip()
            if "-" in route:
                origin, destination = route.split("-", 1)  # Limit the split to only one occurrence
                origin, destination = origin.strip(), destination.strip()
            else:
                origin, destination = "", route.strip()
            routes_data[callsign.strip()] = (origin, destination)
    return routes_data

def main():
    routes_file = "C:/Users/obite/Desktop/12RC/rute.csv"
    airports_file = "C:/Users/obite/Desktop/12RC/airports.csv"  # Change the file path if necessary
    url = "http://atc.avioradar.net/VirtualRadar/AircraftList.json"

    routes_data = read_routes_data(routes_file)  # Read data from the CSV file

    airports_data = {}
    with open(airports_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            icao_code, airport = row  # Since the CSV contains only ICAO code and airport name
            airports_data[icao_code] = airport

    try:
        while True:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Check if the request was successful

                data = response.json()["acList"]
                print("Data fetched successfully!")

                for flight in data:
                    callsign = flight.get("Call")
                    origin, destination = routes_data.get(callsign, ("", ""))
                    if not origin or not destination:
                        continue

                    lat_dubrovnik, lon_dubrovnik = 42.5614, 18.2682
                    lat_aircraft, lon_aircraft = flight.get("Lat"), flight.get("Long")
                    distance_nm = get_distance(lat_dubrovnik, lon_dubrovnik, lat_aircraft, lon_aircraft)

                    status = get_flight_status(flight, destination)

                    print(f"{callsign}, {status}, {destination if destination == 'Dubrovnik' else 'From Dubrovnik'}, Distance: {distance_nm:.2f} NM", flush=True)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")

            time.sleep(10)  # Add a delay of 10 seconds between each loop iteration

    except KeyboardInterrupt:
        print("Script interrupted by user.")

if __name__ == "__main__":
    main()
