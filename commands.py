import time, aiohttp
import urllib.parse


async def process_commands(response, cmd:str):
		
		cmd = cmd.lower()

		if cmd == 'ping':
			ini = time.time() 
			response.message("Pong!")
			fin = time.time() 
			response.message(f"Latency: {(fin-ini)*1000}ms")
			
		if cmd.split(" ", 1)[0] == "weather":
			link = f'https://api.openweathermap.org/data/2.5/weather?q={cmd.split(" ", 1)[1]}&appid=0b821119cc3f23de74aabc092b761984'
			location = {cmd.split(" ", 1)[1]}
			
			async with aiohttp.ClientSession() as session:
				async with session.get(link) as r:
					if r.status == 200:
							res = await r.json()
					else:
							return response.message(f"No location named, *{location}*")
			
			location = res['name']
			lat = res['coord']['lat']
			lon = res['coord']['lon']
			weather = res['weather'][0]['main']
			max_temp = res['main']['temp_max'] - 273.5
			min_temp = res['main']['temp_min'] - 273.5
			press = res['main']['pressure'] / 1000
			humidity = res['main']['humidity']
			visiblity = res['visibility']
			wind_speed = res['wind']['speed']

			country = res['sys']['country']

			response.message(f"Weather at {location}\n\n```Lat:``` *{lat}*\n```Lon:``` *{lon}*\n\n"
											f"```Max:``` *{round(max_temp)}*\n```Min:``` *{round(min_temp)}*\n\n"
											f"```Weather   :``` *{weather}*\n\n"
											f"```Pressure  :``` *{press}*\n"
											f"```Humidity  :``` *{humidity}*\n"
											f"```Visiblity :``` *{visiblity}*\n"
											f"```Wind Speed:``` *{wind_speed}*\n"
											f"```Country   :``` *{country}*")
		
		if (cmd.split(" ", 1)[0] == "calculator") or (cmd.split(" ", 1)[0] == "calc"):
			new_text = urllib.parse.quote(cmd.split(" ", 1)[1])
			link = 'http://twitch.center/customapi/math?expr=' + new_text

			async with aiohttp.ClientSession() as session:
					async with session.get(link) as r:
							if r.status == 200:
									res = await r.text()
							else: return
			if res == '???': msg = "Make sure you use proper syntax"
			response.message(f"Calculated!\n\nAnswer: ```{res if res != '???' else None}```\n\n{msg}")

		#if cmd.split(" ", 1)[0] == 
