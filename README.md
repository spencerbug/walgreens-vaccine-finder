# walgreens-vaccine-finder
Just a quick selenium script to find nearby covid vaccines at walgreens and register the closest one within a certain radius. Enter your information in the config.json

# to set up:
python 3.8

pipenv install

pipenv shell

Rename config_template.json as just config.json

Fill out all the information on the JSON form, you will need a walgreens account, and a twilio account for text message notifications. You'll need to register your phone number with twilio to receive automated sms alerts

# to use
python walgreens.py
