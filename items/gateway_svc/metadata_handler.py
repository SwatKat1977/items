"""
Copyright 2025 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import dataclasses
import json
import logging
import os
import zoneinfo
import jsonschema
import tzlocal
from threadsafe_configuration import ThreadSafeConfiguration as Configuration

TIME_ZONES = [
    {"display": "American Samoa", "id": "US/Samoa"},
    {"display": "Midway Island", "id": "Pacific/Midway"},
    {"display": "Hawaii", "id": "Pacific/Honolulu"},
    {"display": "Alaska", "id": "America/Anchorage"},
    {"display": "Pacific Time (US and Canada)", "id": "America/Los_Angeles"},
    {"display": "Tijuana", "id": "America/Tijuana"},
    {"display": "Arizona", "id": "America/Phoenix"},
    {"display": "Mazatlan", "id": "America/Mazatlan"},
    {"display": "Mountain Time (US and Canada)", "id": "America/Denver"},
    {"display": "Central America", "id": "America/Guatemala"},
    {"display": "Central Time (US and Canada)", "id": "America/Chicago"},
    {"display": "Chihuahua", "id": "America/Chihuahua"},
    {"display": "Guadalajara", "id": "America/Chicago"},
    {"display": "Mexico City", "id": "America/Mexico_City"},
    {"display": "Monterey", "id": "America/Monterrey"},
    {"display": "Saskatchewan", "id": "Canada/Saskatchewan"},
    {"display": "Bogota", "id": "America/Bogota"},
    {"display": "Eastern Time (US and Canada)", "id": "America/New_York"},
    {"display": "Indiana (East)", "id": "America/Indiana/Indianapolis"},
    {"display": "Lima", "id": "America/Lima"},
    {"display": "Quito", "id": "America/Lima"},
    {"display": "Atlantic Time (Canada)", "id": "EST"},
    {"display": "Caracas", "id": "America/Caracas"},
    {"display": "Georgetown", "id": "America/La_Paz"},
    {"display": "La_Paz", "id": "America/La_Paz"},
    {"display": "Costa Rica", "id": "America/Costa_Rica"},
    {"display": "Santiago", "id": "America/Santiago"},
    {"display": "Newfoundland", "id": "America/St_Johns"},
    {"display": "Brasilia", "id": "America/Sao_Paulo"},
    {"display": "Buenos Aires", "id": "America/Buenos_Aires"},
    {"display": "Montevideo", "id": "America/Montevideo"},
    {"display": "Greenland", "id": "America/Godthab"},
    {"display": "Mid-Atlantic", "id": "Atlantic/South_Georgia"},
    {"display": "Azores", "id": "Atlantic/Azores"},
    {"display": "Cape Verde", "id": "Atlantic/Cape_Verde"},
    {"display": "Lisbon", "id": "Europe/London"},
    {"display": "London", "id": "Europe/London"},
    {"display": "Asuncion", "id": "America/Asuncion"},
    {"display": "Cuiaba", "id": "America/Cuiaba"},
    {"display": "Monrovia", "id": "Africa/Monrovia"},
    {"display": "UTC", "id": "UTC"},
    {"display": "Amsterdam", "id": "Europe/Berlin"},
    {"display": "Belgrade", "id": "Europe/Belgrade"},
    {"display": "Berlin", "id": "Europe/Berlin"},
    {"display": "Bern", "id": "Europe/Berlin"},
    {"display": "Bratislava", "id": "Europe/Berlin"},
    {"display": "Brussels", "id": "Europe/Brussels"},
    {"display": "Budapest", "id": "Europe/Berlin"},
    {"display": "Casablanca", "id": "Africa/Casablanca"},
    {"display": "Copenhagen", "id": "Europe/Copenhagen"},
    {"display": "Dublin", "id": "Europe/Dublin"},
    {"display": "Ljubljana", "id": "Europe/Ljubljana"},
    {"display": "Madrid", "id": "Europe/Madrid"},
    {"display": "Paris", "id": "Europe/Paris"},
    {"display": "Prague", "id": "Europe/Prague"},
    {"display": "Rome", "id": "Europe/Rome"},
    {"display": "Sarajevo", "id": "Europe/Sarajevo"},
    {"display": "Sarajevo", "id": "Europe/Skopje"},
    {"display": "Stockholm", "id": "Europe/Stockholm"},
    {"display": "Vienna", "id": "Europe/Vienna"},
    {"display": "Warsaw", "id": "Europe/Warsaw"},
    {"display": "West Central Africa", "id": "Africa/Lagos"},
    {"display": "Zagreb", "id": "Europe/Zagreb"},
    {"display": "Zurich", "id": "Europe/Zurich"},
    {"display": "Athens", "id": "Europe/Athens"},
    {"display": "Bucharest", "id": "Europe/Bucharest"},
    {"display": "Cairo", "id": "Africa/Cairo"},
    {"display": "Harare", "id": "Africa/Harare"},
    {"display": "Helsinki", "id": "Europe/Helsinki"},
    {"display": "Jerusalem", "id": "Asia/Jerusalem"},
    {"display": "Kaliningrad", "id": "Europe/Kaliningrad"},
    {"display": "Kyiv", "id": "Europe/Kyiv"},
    {"display": "Riga", "id": "Europe/Riga"},
    {"display": "Sofia", "id": "Europe/Sofia"},
    {"display": "Tallinn", "id": "Europe/Tallinn"},
    {"display": "Vilnius", "id": "Europe/Vilnius"},
    {"display": "Baghdad", "id": "Asia/Baghdad"},
    {"display": "Istanbul", "id": "Asia/Istanbul"},
    {"display": "Kuwait", "id": "Asia/Kuwait"},
    {"display": "Minsk", "id": "Europe/Minsk"},
    {"display": "Moscow", "id": "Europe/Moscow"},
    {"display": "Nairobi", "id": "Africa/Nairobi"},
    {"display": "Riyadh", "id": "Asia/Riyadh"},
    {"display": "St. Petersburg", "id": "Europe/Moscow"},
    {"display": "Volgograd", "id": "Europe/Volgograd"},
    {"display": "Tehran", "id": "Asia/Tehran"},
    {"display": "Abu Dhabi", "id": "Asia/Dubai"},
    {"display": "Baku", "id": "Asia/Baku"},
    {"display": "Muscat", "id": "Asia/Muscat"},
    {"display": "Muscat", "id": "Asia/Muscat"},
    {"display": "Samara", "id": "Europe/Samara"},
    {"display": "Tbilisi", "id": "Asia/Tbilisi"},
    {"display": "Yerevan", "id": "Asia/Yerevan"},
    {"display": "Kabul", "id": "Asia/Kabul"},
    {"display": "Almaty", "id": "Asia/Almaty"},
    {"display": "Astana", "id": "Asia/Almaty"},
    {"display": "Yekaterinburg", "id": "Asia/Yekaterinburg"},
    {"display": "Islamabad", "id": "Asia/Karachi"},
    {"display": "Karachi", "id": "Asia/Karachi"},
    {"display": "Tashkent", "id": "Asia/Tashkent"},
    {"display": "Chennai", "id": "Asia/Kolkata"},
    {"display": "Kolkata", "id": "Asia/Kolkata"},
    {"display": "Mumbai", "id": "Asia/Kolkata"},
    {"display": "New Delhi", "id": "Asia/Kolkata"},
    {"display": "Sri Jayawardenepura", "id": "Asia/Colombo"},
    {"display": "Kathmandu", "id": "Asia/Kathmandu"},
    {"display": "Dhaka", "id": "Asia/Dhaka"},
    {"display": "Urumqi", "id": "Asia/Urumqi"},
    {"display": "Rangoon", "id": "Asia/Rangoon"},
    {"display": "Bangkok", "id": "Asia/Bangkok"},
    {"display": "Hanoi", "id": "Asia/Bangkok"},
    {"display": "Jakarta", "id": "Asia/Bangkok"},
    {"display": "Krasnoyarsk", "id": "Asia/Krasnoyarsk"},
    {"display": "Novosibirsk", "id": "Asia/Novosibirsk"},
    {"display": "Beijing", "id": "Asia/Shanghai"},
    {"display": "Chongqing", "id": "Asia/Chongqing"},
    {"display": "Hong Kong", "id": "Hongkong"},
    {"display": "Irkutsk", "id": "Asia/Irkutsk"},
    {"display": "Kuala Lumpur", "id": "Asia/Kuala_Lumpur"},
    {"display": "Perth", "id": "Australia/Perth"},
    {"display": "Singapore", "id": "Singapore"},
    {"display": "Taipei", "id": "Asia/Taipei"},
    {"display": "Ulaanbaatar", "id": "Asia/Ulaanbaatar"},
    {"display": "Osaka", "id": "Asia/Tokyo"},
    {"display": "Sapporo", "id": "Asia/Tokyo"},
    {"display": "Seoul", "id": "Asia/Seoul"},
    {"display": "Tokyo", "id": "Asia/Tokyo"},
    {"display": "Yakutsk", "id": "Asia/Yakutsk"},
    {"display": "Adelaide", "id": "Australia/Adelaide"},
    {"display": "Darwin", "id": "Australia/Darwin"},
    {"display": "Brisbane", "id": "Australia/Brisbane"},
    {"display": "Canberra", "id": "Australia/Canberra"},
    {"display": "Guam", "id": "Pacific/Guam"},
    {"display": "Hobart", "id": "Australia/Hobart"},
    {"display": "Melbourne", "id": "Australia/Melbourne"},
    {"display": "Port Moresby", "id": "Pacific/Port_Moresby"},
    {"display": "Sydney", "id": "Australia/Sydney"},
    {"display": "Vladivostok", "id": "Asia/Vladivostok"},
    {"display": "Magadan", "id": "Asia/Magadan"},
    {"display": "New Caledonia", "id": "Pacific/Guadalcanal"},
    {"display": "Solomon Islands", "id": "Pacific/Guadalcanal"},
    {"display": "Srednekolymsk", "id": "Asia/Srednekolymsk"},
    {"display": "Auckland", "id": "Pacific/Auckland"},
    {"display": "Fiji, Marshall Islands", "id": "Pacific/Fiji"},
    {"display": "Kamchatka", "id": "Asia/Kamchatka"},
    {"display": "Marshall Islands", "id": "Pacific/Fiji"},
    {"display": "Wellington", "id": "Pacific/Auckland"},
    {"display": "Chatham", "id": "Pacific/Chatham"},
    {"display": "Nuku'alofa", "id": "Pacific/Tongatapu"},
    {"display": "Samoa", "id": "Pacific/Apia"},
]

VALID_TIME_ZONES_IDS: set = {tz['id'].upper() for tz in TIME_ZONES}

DEFAULT_TIME_ZONE_DEFAULT: str = "_server_tz_"
SECTION_SERVER_SETTINGS: str = "server_settings"
SERVER_SETTINGS_INSTANCE_NAME: str = "instance_name"
SERVER_SETTINGS_DEFAULT_TIME_ZONE: str = "default_time_zone"


@dataclasses.dataclass
class MetadataSettings:
    default_time_zone: str = ""
    using_server_default_time_zone: bool = False
    instance_name: str = ""


METADATA_FILE_SCHEMA: dict = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    SECTION_SERVER_SETTINGS: {
      "type": "object",
      "properties": {
        SERVER_SETTINGS_INSTANCE_NAME: {
          "type": "string"
        },
        SERVER_SETTINGS_DEFAULT_TIME_ZONE: {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [SERVER_SETTINGS_INSTANCE_NAME,
                   SERVER_SETTINGS_DEFAULT_TIME_ZONE],
      "additionalProperties": False
    }
  },
  "required": [SECTION_SERVER_SETTINGS],
  "additionalProperties": False
}


class MetadataHandler:

    def __init__(self, logger: logging.Logger):
        self._logger = logger.getChild(__name__)
        self.metadata_settings: MetadataSettings = MetadataSettings()

    def read_metadata_file(self) -> bool:
        config_file: str = Configuration().general_metadata_config_file

        if not os.path.exists(config_file):
            self._logger.critical("Metadata config file '%s' cannot be opened",
                                  config_file)
            return False

        try:
            with open(config_file, 'r') as file:
                config_data = json.load(file)

        except (TypeError, json.JSONDecodeError):
            self._logger.critical("The JSON file is not properly formatted.")
            return False

        except IOError as ex:
            self._logger.critical("An IO error occurred: %s", str(ex))
            return False

        try:
            jsonschema.validate(instance=config_data,
                                schema=METADATA_FILE_SCHEMA)

        except jsonschema.exceptions.ValidationError:
            self._logger.critical(("Metadata config file failed JSON schema "
                                  "validation"))
            return False

        server_settings: dict = config_data[SECTION_SERVER_SETTINGS]
        time_zone: str = server_settings[SERVER_SETTINGS_DEFAULT_TIME_ZONE]
        instance_name: str = server_settings[SERVER_SETTINGS_INSTANCE_NAME]

        if time_zone == DEFAULT_TIME_ZONE_DEFAULT:
            # Get the system's timezone name in a zoneinfo-compatible format
            # and the read it using zoneinfo.
            server_tz_name = tzlocal.get_localzone_name()
            server_tz = zoneinfo.ZoneInfo(server_tz_name)

            if server_tz_name.upper() not in VALID_TIME_ZONES_IDS:
                self._logger.critical("Unable to get server timezone, aborting...")
                return False

            self.metadata_settings.default_time_zone = server_tz_name
            self.metadata_settings.using_server_default_time_zone = True

            self._logger.info("Default server time zone: (Server): %s",
                              server_tz_name)

        else:
            if time_zone.upper() not in VALID_TIME_ZONES_IDS:
                self._logger.critical(
                    ("Default server time zone (%s) in metadata configuration "
                     "is not a valid time zone!"), time_zone)
                return False

            self.metadata_settings.default_time_zone = time_zone
            self.metadata_settings.using_server_default_time_zone = False

            self._logger.info("Default server time zone: (From file): %s",
                              time_zone)

        self.metadata_settings.instance_name = instance_name
        self._logger.info("Server instance name: %s",
                          self.metadata_settings.instance_name)

        return True
