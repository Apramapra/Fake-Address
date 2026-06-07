import os
from flask import Flask, request, jsonify
from faker import Faker
from faker.config import AVAILABLE_LOCALES
from unidecode import unidecode

app = Flask(__name__)
app.json.ensure_ascii = False

# Country name -> locale for names/phones (native script)
COUNTRY_LOCALE = {
    'india': 'hi_IN',
    'iran': 'fa_IR',
    'japan': 'ja_JP',
    'germany': 'de_DE',
    'france': 'fr_FR',
    'usa': 'en_US',
    'uk': 'en_GB',
    # Add more countries as needed – see the full list from earlier versions
}

# Country name -> English locale for address (perfect English)
ENGLISH_ADDRESS_LOCALE = {
    'india': 'en_IN',
    'usa': 'en_US',
    'uk': 'en_GB',
    'canada': 'en_CA',
    'australia': 'en_AU',
}

def get_address_faker(country_name):
    """Returns a Faker instance that generates English addresses."""
    key = country_name.lower().strip()
    if key in ENGLISH_ADDRESS_LOCALE:
        return Faker(ENGLISH_ADDRESS_LOCALE[key])
    if key in COUNTRY_LOCALE:
        return Faker(COUNTRY_LOCALE[key])  # will be transliterated later
    return Faker('en_US')  # fallback

@app.route('/fake', methods=['GET'])
def fake_person_and_address():
    country_param = request.args.get('country')
    if not country_param:
        return jsonify({'error': 'Missing country'}), 400

    country_lower = country_param.lower().strip()
    
    if country_lower not in COUNTRY_LOCALE:
        return jsonify({'error': f'Country "{country_param}" not supported'}), 400

    native_faker = Faker(COUNTRY_LOCALE[country_lower])
    first_name = native_faker.first_name()
    last_name = native_faker.last_name()
    phone_number = native_faker.phone_number()

    addr_faker = get_address_faker(country_lower)
    street = addr_faker.street_address()
    city = addr_faker.city()
    if hasattr(addr_faker, 'state'):
        state = addr_faker.state()
    elif hasattr(addr_faker, 'administrative_unit'):
        state = addr_faker.administrative_unit()
    else:
        state = ''
    zipcode = addr_faker.postcode()
    country = addr_faker.current_country()

    if country_lower not in ENGLISH_ADDRESS_LOCALE:
        street = unidecode(street)
        city = unidecode(city)
        state = unidecode(state)
        zipcode = unidecode(zipcode)
        country = unidecode(country)

    full = f"{street}, {city}, {state} {zipcode}".strip()
    response = {
        'locale': COUNTRY_LOCALE[country_lower],
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'address': {
            'street': street,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'country': country,
            'full_address': full
        }
    }
    return jsonify(response)

@app.route('/countries', methods=['GET'])
def list_countries():
    return jsonify({
        'supported_countries': list(COUNTRY_LOCALE.keys()),
        'english_address_countries': list(ENGLISH_ADDRESS_LOCALE.keys())
    })

if __name__ == '__main__':
    # Use the PORT environment variable (Render sets this) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # In production, gunicorn will run the app; this block is for local testing only
    app.run(host='0.0.0.0', port=port)
