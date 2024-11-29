# HomeAssistant Smarthub energy sensor

This is a custom integration used to scrape data from a smarthub portal (used by different energy providers), and create an energy usage sensor in Home Assistant. The sensor can then be used with the Energy dashboard.

# Setup

## Manual installation

Clone this repository in your home assistant's `custom_components` directory:
```
git clone git@github.com:gagata/ha-smarthub-energy-sensor.git
```

## Configuration

Go to Settings > Devices & services and click +Add integration, and search for Smarthub.

The wizard will ask for:
- email address used to log in to the portal
- user password
- host (most likely `<your_provider>.smarthub.coop`)
- your account id (taken from the billing)
- your **location id** (instruction below)


**Getting the location id**

- This value can be retrieved using `Network` tab in Developer Tools in your browser.
- Navigate to Usage Explorer page, find a call to `services/secured/utility-usage/poll` in the `Network` tab.
- Open the call, and copy the `serviceLocationNumber` field from the `Payload` tab.


# Credits
Thanks [@tedpearson](https://github.com/tedpearson) for his [go implementation](https://github.com/tedpearson/electric-usage-downloader) which inspired this integration.

# This sucks, can you even write proper HA integrations?
Nope, and I don't intend to, as I genuinely despise Python. Feel free to use as is, but I'll also happily accept PRs to make this thing better :)
