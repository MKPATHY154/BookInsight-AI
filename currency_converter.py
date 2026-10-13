
import requests
from config import SUPPORTED_CURRENCIES

API_URL = "https://open.er-api.com/v6/latest/GBP"


def get_exchange_rates():
    """Fetch exchange rates with GBP as the base currency."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("result") != "success":
            raise ValueError("Exchange-rate service returned an error.")

        return data["rates"]

    except (requests.RequestException, ValueError, KeyError) as error:
        print("Could not fetch exchange rates:", error)
        return None


def convert_price(amount, from_currency, to_currency, rates):
    """Convert an amount using rates relative to GBP."""
    if rates is None:
        raise ValueError("Exchange rates are unavailable.")

    if from_currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Unsupported source currency.")

    if to_currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Unsupported target currency.")

    if from_currency not in rates or to_currency not in rates:
        raise ValueError("Required exchange rate is unavailable.")

    amount_in_gbp = amount / rates[from_currency]
    converted_amount = amount_in_gbp * rates[to_currency]

    return round(converted_amount, 2)


if __name__ == "__main__":
    rates = get_exchange_rates()

    if rates:
        print("Exchange rates loaded successfully.")

        price_inr = convert_price(100, "GBP", "INR", rates)
        print("£100 converted to INR:", price_inr)
