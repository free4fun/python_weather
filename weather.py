# weather.py
# Author Mauricio Sosa Giri <free4fun@riseup.net>

import argparse;
import json;
import sys;
import datetime;
from configparser import ConfigParser;
from urllib import error, parse, request;

import style;

BASE_WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather";

# Weather Condition Codes
# https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
THUNDERSTORM = range(200, 300);
DRIZZLE = range(300, 400);
RAIN = range(500, 600);
SNOW = range(600, 700);
ATMOSPHERE = range(700, 800);
CLEAR = range(800, 801);
CLOUDY = range(801, 900);

#compass Rose
NORTHEAST = range(23, 68);
EAST = range(68, 113);
SOUTHEAST = range(113, 158);
SOUTH = range(158, 203);
SOUTHWEST = range(203, 248);
WEST = range(248, 293);
NORTHWEST = range(293, 338);
NORTH = [*range(0, 23), *range(338, 361)];

def read_user_cli_args():
    """Handles the CLI user interactions.
    Returns:
        argparse.Namespace: Populated namespace object
    """
    parser = argparse.ArgumentParser(
        description="gets weather and temperature information for a city"
    );
    parser.add_argument(
        "city", nargs=1, type=str, help="enter the city name"
    );
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="display the weather in imperial units",
    );
    parser.add_argument(
        "-l",
        "--language",
        nargs="?",
        type=str,
        default='en',
        help="two letters abbreviation of language to be display",
    );
    return parser.parse_args();
def build_weather_query(city_input, language_input, imperial=False):
    """Builds the URL for an API request to OpenWeather's weather API.
    Args:
        city_input (List[str]): Name of a city as collected by argparse
        imperial (bool): Whether or not to use imperial units for temperature
        lang (List[str]): Two letter abbreviation of language to be display
    Returns:
        str: URL formatted for a call to OpenWeather's city name endpoint
    """
    api_key = _get_api_key();
    city_name = " ".join(city_input);
    language = " ".join(language_input);
    url_encoded_city_name = parse.quote_plus(city_name);
    units = "imperial" if imperial else "metric";
    url = (
        f"{BASE_WEATHER_API_URL}?q={url_encoded_city_name}"
        f"&lang={language_input}&units={units}&APPID={api_key}"
    );
    return url;

def _get_api_key():
    """Fetch the API key from your configuration file.
    Expects a configuration file named "secrets.ini" with structure:
        [openweather]
        api_key=<YOUR-OPENWEATHER-API-KEY>
    """
    config = ConfigParser();
    config.read("secrets.ini");
    return config["openweather"]["api_key"];

def get_weather_data(query_url):
    """Makes an API request to a URL and returns the data as a Python object.
    Args:
        query_url (str): URL formatted for OpenWeather's city name endpoint
    Returns:
        dict: Weather information for a specific city
    """
    try:
        response = request.urlopen(query_url);
    except error.HTTPError as http_error:
        if http_error.code == 401:  # 401 - Unauthorized
            sys.exit("Access denied. Check your API key.");
        elif http_error.code == 404:  # 404 - Not Found
            sys.exit("Can't find weather data for this city.");
        else:
            sys.exit(f"Something went wrong... ({http_error.code})");
    data = response.read();
    try:
        return json.loads(data);
    except json.JSONDecodeError:
        sys.exit("Couldn't read the server response.");

def display_weather_info(weather_data, imperial=False):
    """Prints formatted weather information about a city.
    Args:
    weather_data (dict): API response from OpenWeather by city name
    imperial (bool): Whether or not to use imperial units for temperature
    More information at https://openweathermap.org/current#name
    """
    city = weather_data["name"];
    country = weather_data["sys"]["country"];
    long = weather_data["coord"]["lon"];
    lat = weather_data["coord"]["lat"];
    weather_id = weather_data["weather"][0]["id"];
    weather_description = weather_data["weather"][0]["description"];
    temperature = weather_data["main"]["temp"];
    feels_like = weather_data["main"]["feels_like"];
    pressure = weather_data["main"]["pressure"];
    humidity = weather_data["main"]["humidity"];
    wind_speed = weather_data["wind"]["speed"];
    wind_degrees = weather_data["wind"]["deg"];
    if "gust" in weather_data["wind"]:
        gust = weather_data["wind"]["gust"];
    else:
        gust = 0;
    current_time = datetime.datetime.fromtimestamp(weather_data["dt"]);
    sunrise = datetime.datetime.fromtimestamp(weather_data["sys"]["sunrise"]);
    sunset = datetime.datetime.fromtimestamp(weather_data["sys"]["sunset"]);
    timezone = round(weather_data["timezone"]/3600,1);


    style.change_color(style.REVERSE);
    print(f"{city+', '+ country:^{style.PADDING}}", end=" ");
    style.change_color(style.RESET);

    weather_symbol, color = _select_weather_display_params(weather_id);
    wind_direction, wind_symbol = _select_wind_direction(wind_degrees);
    longitude, latitude = _select_location(long, lat);
    style.change_color(color);
    print(f"\t{weather_symbol}", end=" ");
    print(f"{weather_description.capitalize()}");
    style.change_color(style.RESET);
    print(f"Update: {current_time.strftime('%d/%m/%Y - %H%M%S')}.");
    print(f"Temp: {round(temperature)}°{'F' if imperial else 'C'}. Feels like: {round(feels_like)}°{'F' if imperial else 'C'}.");
    print(f"Pressure: {round(pressure)}hPa. Humidity: {round(humidity)}%.");
    print(f"Wind: {wind_symbol} {wind_speed if imperial else round(wind_speed*3.6,1)}{'mph' if imperial else 'Km/h'} from {wind_direction}. Gusts: {gust if imperial else round(gust*3.6,0)} {'mph' if imperial else 'Km/h.'}");
    print(f"Sunrise: {sunrise.strftime('%d/%m/%Y - %H:%M')}. Sunset: {sunset.strftime('%d/%m/%Y - %H:%M')}. Timezone: {round(timezone)} GMT.");
    print(f"Coordinates: {longitude}. {latitude}. Map: https://osm.org/?mlat={lat}&mlon={long}");


def _select_weather_display_params(weather_id):
    if weather_id in THUNDERSTORM:
        display_params = ("⚡️", style.RED);
    elif weather_id in DRIZZLE:
        display_params = ("💧", style.CYAN);
    elif weather_id in RAIN:
        display_params = ("🌧", style.BLUE);
    elif weather_id in SNOW:
        display_params = ("❄️", style.WHITE);
    elif weather_id in ATMOSPHERE:
        display_params = ("🌪", style.BLUE);
    elif weather_id in CLEAR:
        display_params = ("☀️", style.YELLOW);
    elif weather_id in CLOUDY:
        display_params = ("☁️", style.WHITE);
    else:  # In case the API adds new weather codes
        display_params = ("🌈", style.RESET);
    return display_params;

def _select_wind_direction(wind_degrees):
    if wind_degrees in NORTHEAST:
        wind_direction = ("Northeast","↘️");
    elif wind_degrees in EAST:
        wind_direction = ("East","⬅️");
    elif wind_degrees in SOUTHEAST:
        wind_direction = ("Southeast","↗️");
    elif wind_degrees in SOUTH:
        wind_direction = ("South","⬆️");
    elif wind_degrees in SOUTHWEST:
        wind_direction = ("Southwest","↖️");
    elif wind_degrees in WEST:
        wind_direction = ("West","➡️");
    elif wind_degrees in NORTHWEST:
        wind_direction = ("Northwest","↙️");
    elif wind_degrees in NORTH:
        wind_direction = ("North","⬇️");
    else: #Wind went crazy!
        wind_direction = ("Crazy!","🔄");
    return wind_direction;

def _select_location(long, lat):
    if (long < 0):
        long = str(abs(long))+" West";
    else:
        long = str(long)+" East";
    if (lat < 0):
        lat = str(abs(lat))+" South";
    else:
        long = str(long)+" North";
    return (long, lat);

if __name__ == "__main__":
    user_args = read_user_cli_args();
    query_url = build_weather_query(user_args.city, user_args.language, user_args.imperial);
    weather_data = get_weather_data(query_url);
    display_weather_info(weather_data, user_args.imperial)
