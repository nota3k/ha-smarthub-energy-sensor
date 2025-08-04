import aiohttp
from datetime import datetime, timedelta
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

def parse_last_usage(data):
    """
    Parse the JSON data and extract the last data point for usage.

    Args:
        data (dict): The JSON data as a Python dictionary.

    Returns:
        dict: A dictionary containing the timestamp and value of the last usage point.
    """
    result = {}
    
    try:
        # Locate the "ELECTRIC" data
        electric_data = data.get("data", {}).get("ELECTRIC", [])
        
        for entry in electric_data:
            entry_type = entry.get("type")
            
            # Find the entry with type "USAGE"
            if entry_type == "USAGE":
                series = entry.get("series", [])
                for serie in series:
                    # Extract the last data point in the "data" array
                    usage_data = serie.get("data", [])
                    if usage_data:
                        last_data_point = usage_data[-1]
                        value = last_data_point.get("y")
                        result["current_energy_usage"] = value
                        
            # Find the entry with type "COST" for cost data
            elif entry_type == "COST":
                series = entry.get("series", [])
                for serie in series:
                    # Extract the last data point in the "data" array
                    cost_data = serie.get("data", [])
                    if cost_data:
                        last_cost_point = cost_data[-1]
                        cost_value = last_cost_point.get("y")
                        result["current_energy_cost"] = cost_value

        # Return the result if we found any data
        return result if result else None
        
    except Exception as e:
        _LOGGER.error("Error parsing usage data: %s", e)
        raise RuntimeError(f"Error parsing usage data: {e}")

class SmartHubAPI:
    """Class to interact with the SmartHub API."""

    def __init__(self, email, password, account_id, location_id, host):
        self.email = email
        self.password = password
        self.account_id = account_id
        self.location_id = location_id
        self.host = host
        self.token = None

    async def get_token(self):
        """Authenticate and retrieve the token asynchronously."""
        auth_url = f"https://{self.host}/services/oauth/auth/v2"
        headers = {
            "Authority": self.host,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = f"password={self.password}&userId={self.email}"

        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, headers=headers, data=payload) as response:
                response_text = await response.text()

                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to retrieve authorization token. HTTP Status: {response.status}"
                    )

                response_json = await response.json()
                self.token = response_json.get("authorizationToken")
                if not self.token:
                    raise RuntimeError("Failed to retrieve authorization token.")

    async def get_energy_data(self):
        """Retrieve energy usage data asynchronously with retry logic."""
        await self.get_token()

        poll_url = f"https://{self.host}/services/secured/utility-usage/poll"
        headers = {
            "Authority": self.host,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Nisc-Smarthub-Username": self.email,
        }

        # Calculate startDateTime and endDateTime
        # Revert to original working timeframe that was proven to work
        now = datetime.now()
        end_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=30) + timedelta(hours=1)

        start_timestamp = int(start_time.timestamp()) * 1000
        end_timestamp = int(end_time.timestamp()) * 1000

        data = {
            "timeFrame": "MONTHLY",  # Revert to MONTHLY which was working
            "userId": self.email,
            "screen": "USAGE_EXPLORER",
            "includeDemand": False,
            "serviceLocationNumber": self.location_id,
            "accountNumber": self.account_id,
            "industries": ["ELECTRIC"],
            "startDateTime": str(start_timestamp),
            "endDateTime": str(end_timestamp),
        }

        max_retries = 5  # Maximum number of retries
        retry_delay = 2  # Delay between retries in seconds

        for attempt in range(1, max_retries + 1):
            async with aiohttp.ClientSession() as session:
                async with session.post(poll_url, headers=headers, json=data) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        raise RuntimeError(
                            f"Failed to retrieve energy data. HTTP Status: {response.status}"
                        )

                    response_json = await response.json()

                    # Check if the status is still pending
                    if response_json.get("status") == "PENDING":
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            _LOGGER.error("Maximum retries reached. Data still PENDING.")
                            raise RuntimeError("Failed to retrieve complete data. Status: PENDING")
                    else:
                        # Valid response received
                        return parse_last_usage(response_json)

        raise RuntimeError("Unexpected error: Retry loop exited without success.")

