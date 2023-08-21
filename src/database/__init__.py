import json, os, time, random, math, sys, discord, math, glob
from datetime import datetime
from datetime import timedelta

# custom blackjack game thing
##from game_libs.blackjack import blackjack_discord_implementation
# custom roulette game thing
##from game_libs.roulette import roulette_discord_implementation

"""

	the database handler of the unbelievaboat-python discord bot
	// is imported by ../main.py

"""


class pythonboat_database_handler:
	# always called when imported in main.py
	def __init__(self, client):
		# we do the path from the main.py file, so we go into the db folder, then select
		self.pathToJson = "/root/BBTCG/PROD/Discord-TCG/src/database/database.json"
		self.client = client

		# for colors
		self.discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
		self.discord_blue_rgb_code = discord.Color.from_rgb(3, 169, 244)
		self.discord_success_rgb_code = discord.Color.from_rgb(102, 187, 106)

		# check if file is created, else create it
		if not os.path.exists(self.pathToJson):
			creating_file = open(self.pathToJson, "w")
			# adding default json config into the file if creating new
			# all the users will get created automatically in the function self.find_index_in_db()
			# but for the different jobs etc the program needs configs for variables and symbols
			creating_file.write("""{\n\t"userdata": [],
										"variables": [],
										"symbols": [
											{"name":"currency_symbol","symbol_emoji":":dollar:"}
										],
										"items": [
											{}
										],
										"income_roles": [
											{}
										]
										\n}""")
			creating_file.close()

	#

	# check if json file is corrupted
	#  -> in self.check_json()
	# called from main.py

	def get_currency_symbol(self, test=False, value="unset"):
		if not test:
			# get currency symbol to use
			temp_json_opening = open(self.pathToJson, "r")
			temp_json_content = json.load(temp_json_opening)
			# the currency symbol is always at position 0 in the "symbols" part
			currency_symbol = temp_json_content["symbols"][0]["symbol_emoji"]
			self.currency_symbol = discord.utils.get(self.client.emojis, name=currency_symbol)
		else:
			try:
				self.currency_symbol = discord.utils.get(self.client.emojis, name=value)
				print(str(self.currency_symbol))
				if self.currency_symbol == None:
					return "error"
			except:
				return "error"

	# if we handle a already created file, we need certain variables
	async def check_json(self):
		temp_json_opening = open(self.pathToJson, "r")
		temp_json_content = json.load(temp_json_opening)
		"""
		possibly to add :
			improve the error system, raising specific errors with a "error_info"
			for example : "userdata missing", or "slut missing", or even "slut min_revenue missing"
		"""
		try:
			check_content = temp_json_content
			# userdata space
			userdata = check_content["userdata"]
			# variables
			variables = check_content["variables"]
			# symbol
			currency_symbol = check_content["symbols"][0]
			items = check_content["items"]
			roles = check_content["income_roles"]

			# didnt fail, so we're good
			temp_json_opening.close()
		except Exception as e:
			# something is missing, inform client
			return "error"

	"""
	GLOBAL FUNCTIONS
	"""

	# need to overwrite the whole json when updating, luckily the database won't be enormous
	def overwrite_json(self, content):
		self.json_db = open(self.pathToJson, "w")
		self.clean_json = json.dumps(content, indent=4, separators=(",", ": "))
		self.json_db.write(self.clean_json)
		self.json_db.close()

	# find the user in the database
	def find_index_in_db(self, data_to_search, user_to_find, fail_safe=False):
		#print(data_to_search)
		user_to_find = int(user_to_find)
		for i in range(len(data_to_search)):
			if data_to_search[i]["user_id"] == user_to_find:
				print("\nfound user\n")
				return int(i), "none"

		# in this case, this isnt a user which isnt yet registrated
		# but someone who doesnt exist on the server
		# or at least thats what is expected when calling with this parameter
		if fail_safe:
			return 0, "error"

		print("\ncreating user\n")
		# we did NOT find him, which means he doesn't exist yet
		# so we automatically create him
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		data_to_search.append({
			"user_id": user_to_find,
			"cash": 150,
			"engagement": 0,
			# "balance" : cash + bank
			# "roles": "None" ; will be checked when calculating weekly auto-role-income
			"items": "none",
		})
		json_content["userdata"] = data_to_search
		self.overwrite_json(json_content)
		"""
			POSSIBLE ISSUE :
				that we need to create user by overwrite, then problem of doing that while another command is
				supposed to have it open etc. hopefully it works just as such
		"""
		# now that the user is created, re-check and return int

		for i in range(len(data_to_search)):
			if data_to_search[i]["user_id"] == user_to_find:
				return int(i), data_to_search

	"""
	CLIENT-DB HANDLING
	"""
	##########
	## Adding enagagement on non-command messages
	##########

	## TODO: This doesnt fully work yet, it's the actual time passing i need to figure out, then save.
	async def non_command_engagement_boost(self, user):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]

		# new edit for hourly income:
		now = datetime.now()
		last_engagement_update_string = user_content["last_engagement_boost"]
		# get a timeobject from the string
		last_engagement_update = datetime.strptime(last_engagement_update_string, '%Y-%m-%d %H:%M:%S.%f')
		# calculate difference, see if it works
		passed_time = now - last_engagement_update
		passed_time_hours = passed_time.total_seconds() // 3600.0
		passed_time_minutes = passed_time.total_seconds() // 216000.0
		print(f"Non-message: user {user} last message was {last_engagement_update_string}")
		print(f"Non-message: Thats {passed_time.total_seconds()} in total_seconds")
		print(f"Non-message: Thats {passed_time_hours} in hours")
		print(f"Non-message: and   {passed_time_minutes} in minutes")

		## user_content["engagement"] += 1
		return "success"

	#
	# BALANCE
	#

	async def balance(self, user, channel, userbal_to_check, username_to_check, userpfp_to_check):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		# check if user exists
		# no need for fail_safe option because that is already checked in main.py before calling this function
		checked_user, status = self.find_index_in_db(json_content["userdata"], userbal_to_check)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][checked_user]
		check_cash = "{:,}".format(int(json_user_content["cash"]))
		## TODO: Count items, and maybe even total TV?

		formatted_time = str(f"{datetime.now().hour}:{datetime.now().minute}")

		color = self.discord_blue_rgb_code
		embed = discord.Embed(color=color)
		embed.add_field(name="**Cash**", value=f"{str(self.currency_symbol)} {check_cash}", inline=True)
		embed.set_author(name=username_to_check, icon_url=userpfp_to_check)
		embed.set_footer(text=f"today at {formatted_time}")
		await channel.send(embed=embed)

		return

	#
	# GIVE
	#

	async def give(self, user, channel, username, user_pfp, reception_user, amount, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]
		json_recept_content = json_content["userdata"][reception_user_index]

		user_cash = json_user_content["cash"]
		recept_cash = json_recept_content["cash"]

		if amount == "all":
			amount = user_cash
			if amount < 0:
				return "error", "❌ No negative values."
		else:
			amount = int(amount)
			if amount > user_cash:
				return "error", f"❌ You don't have that much money to give. You currently have {str(self.currency_symbol)} {'{:,}'.format(int(user_cash))} in the bank."

		json_user_content["cash"] -= amount
		json_recept_content["cash"] += amount

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ {recept_uname.mention} has received your {str(self.currency_symbol)} {'{:,}'.format(int(amount))}",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_user_content["engagement"] += 4
		json_content["userdata"][user_index] = json_user_content
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# LEADERBOARD
	#

	async def leaderboard(self, user, channel, username, full_name, page_number, mode_type, client):
		# load json
		## TODO: REDO Leaderboard to something neater
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]

		"""
		sorting algorithm
		"""
		# yes, i could use a dict
		all_users = []
		all_bal = []
		i = 0
		for i in range(len(json_content["userdata"])):
			all_users.append(json_content["userdata"][i]["user_id"])
			if mode_type == "-cash":
				all_bal.append(int(json_content["userdata"][i]["cash"]))
			#elif mode_type == "-cards":
			#	all_bal.append(int(json_content["userdata"][i]["items"]))
			else:  # elif mode_type == "-total":
			#	print(json_content["userdata"][i]["cash"] + json_content["userdata"][i]["items"])
				all_bal.append(int(json_content["userdata"][i]["cash"])) #+ json_content["userdata"][i]["items"]))
		print(all_bal)
		# so, data is set, now sort
		i = -1
		while i <= len(all_bal):
			i += 1
			try:
				if all_bal[i] < all_bal[i + 1]:
					# save the higher stats one into buffer
					saved = all_bal[i]
					# this one has lower stats, so move him right
					all_bal[i] = all_bal[i + 1]
					# the higher one (saved) takes that position
					all_bal[i + 1] = saved
					# repeat process, but for the player-names
					saved = all_users[i]
					all_users[i] = all_users[i + 1]
					all_users[i + 1] = saved
					i = -1
			except:
				pass

		i = 0
		# use names instead of just ID, except if we cannot find names
		# so for example if someone left the server
		for i in range(len(all_users)):
			try:
				name_object = await client.fetch_user(int(all_users[i]))
				print(i, all_users[i], name_object)
				actual_name = str(name_object)
				if all_users[i] == user:
					user_lb_position = i + 1
			except:
				actual_name = str(all_users[i])
			# update
			all_users[i] = actual_name

		i = 0
		# making nice number formats
		for i in range(len(all_bal)):
			all_bal[i] = '{:,}'.format(all_bal[i])

		# making the formatted output description
		# number of pages which will be needed :
		# we have 10 ranks per page
		ranks_per_page = 10
		page_count = len(all_bal) / ranks_per_page
		if ".0" in str(page_count): page_count = int(page_count)
		if not isinstance(page_count, int):
			page_count += 1
		# page_count = (len(all_bal) + ranks_per_page - 1)
		# round number up
		total_pages = round(page_count)

		# our selection !
		index_start = (page_number - 1) * ranks_per_page
		index_end = index_start + ranks_per_page
		user_selection = all_users[index_start: index_end]
		bal_selection = all_bal[index_start: index_end]

		# making the formatted !
		i = 0
		leaderboard_formatted = f""
		for i in range(len(user_selection)):
			leaderboard_formatted += f"\n**{str(i + 1)}.** {user_selection[i]} • {str(self.currency_symbol)} {bal_selection[i]}"

		# making a nice output
		if total_pages == 1:
			page_number = 1
		elif page_number > total_pages:
			page_number = 1

		# inform user
		color = self.discord_blue_rgb_code
		embed = discord.Embed(description=f"\n\n{leaderboard_formatted}", color=color)
		# same pfp as unbelievaboat uses
		embed.set_author(name=full_name,
						 icon_url="https://media.discordapp.net/attachments/506838906872922145/506899959816126493/h5D6Ei0.png")
		if user_lb_position == 1:
			pos_name = "st"
		elif user_lb_position == 2:
			pos_name = "nd"
		elif user_lb_position == 3:
			pos_name = "rd"
		embed.set_footer(
			text=f"Page {page_number}/{total_pages}  •  Your leaderboard rank: {user_lb_position}{pos_name}")
		await channel.send(embed=embed)

		return "success", "success"

	#
	# MODULE INFO
	#  TODO: This module command is a bit of a mystery still, gotta learn what it's all about.

	async def module(self, user, channel, module):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		if module not in self.variable_dict.keys() and module not in ["symbols", "currency_symbol"]:
			possible = "symbols"
			return "error", f"Module not found. Possibilites : {possible}"

		if module in ["symbols", "currency_symbol"]:
			info_output = f"""Symbol:\nname: {json_content['symbols'][0]['name']}, value: emoji \"{json_content['symbols'][0]['symbol_emoji']}" """
		else:
			module_index = self.variable_dict[module]
			info_output = f"Module: **{module}** info:\nOutput as : <variable name> ; <value>\n```"
			mod = json_content["variables"][module_index]
			module_content = json_content["variables"][module_index]
			for i in range(len(module_content)):
				module_content_vars = list(json_content["variables"][module_index].keys())[i]

				info_output += f'\n"{module_content_vars}" ; {mod[module_content_vars]}'
			info_output += "\n```\n**Note**: Delay is in minutes, proba is x%, percentages are in % too"
		await channel.send(info_output)

		return "success", "success"

	#
	# ADD-MONEY
	#

	async def add_money(self, user, channel, username, user_pfp, reception_user, amount, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_recept_content = json_content["userdata"][reception_user_index]

		json_recept_content["cash"] += int(amount)

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Added {str(self.currency_symbol)} {'{:,}'.format(int(amount))} to {recept_uname.mention}'s cash balance",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# REMOVE-MONEY
	#

	async def remove_money(self, user, channel, username, user_pfp, reception_user, amount, recept_uname):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)

		if new_data != "none":
			json_content["userdata"] = new_data

		json_recept_content = json_content["userdata"][reception_user_index]

		json_recept_content["cash"] -= int(amount)

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Removed {str(self.currency_symbol)} {'{:,}'.format(int(amount))} from {recept_uname.mention}'s cash balance",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# EDIT VARIABLES
	#

	async def edit_variables(self, user, channel, username, user_pfp, module_name, variable_name, new_value):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		if module_name not in self.variable_dict.keys():
			return "error", "module not found"
		module_index = self.variable_dict[module_name]

		json_module_content = json_content["variables"][module_index]
		try:
			old_value = json_module_content[variable_name]
		except:
			return "error", f"variable name of module {module_name} not found"

		# changing value
		json_module_content[variable_name] = new_value

		# not asking for verification, would just have to reverse by another edit
		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅  Changed variable '{variable_name}' of module '{module_name}'\nBefore: '{old_value}'. Now: '{new_value}'",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["variables"][module_index] = json_module_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# EDIT CURRENCY SYMBOL
	#

	async def change_currency_symbol(self, user, channel, username, user_pfp, new_emoji_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_emoji = json_content["symbols"][0]

		old_value = json_emoji["symbol_emoji"]

		test_emoji = self.get_currency_symbol(True, new_emoji_name)
		if test_emoji == "error":
			return "error", "Emoji not found."

		# changing value
		json_emoji["symbol_emoji"] = new_emoji_name

		# not asking for verification, would just have to reverse by another edit
		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(description=f"✅  Changed emoji from '{old_value}' to '{new_emoji_name}'", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["symbols"][0] = json_emoji
		self.overwrite_json(json_content)

		return "success", "success"

	"""
	ITEM HANDLING
	"""

	#
	# CREATE NEW ITEM
	#

	async def create_new_item(self, item_name, team_name, position, rarity):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		json_items = json_content["items"]

		img_dir = "/root/BBTCG/assets/Season 16/"
		basic_img_dir = img_dir + "Basic/"
		shiny_img_dir = img_dir + "Shiny/"

		## Check for dupes
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				return "error", "Item with such name already exists."

		## Add basic item
		json_items.append({
			"name": item_name,
			"team_name": team_name,
			"season_name": "Season 16",
			"image_location": basic_img_dir + team_name + "/" + item_name + ".png",
			"shiny": False,
			"position": position,
			"deceased": False,
			"rarity": rarity
		})
		json_items.append({
			"name": "Shiny " + item_name,
			"team_name": team_name,
			"season_name": "Season 16",
			"image_location": shiny_img_dir + team_name + "/" + item_name + ".gif",
			"shiny": True,
			"position": position,
			"deceased": False,
			"rarity": rarity
		})

		# overwrite, save current data
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"
	
	## Populate_database will recursivly search the asset folder for NEW images to make as items in it's DB
	async def populate_database(self):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		json_items = json_content["items"]

		img_dir = "/root/BBTCG/assets/"
		files = glob.glob(img_dir + "**", recursive = True) ## Glob finds all filenames
		for item in files:
			split_string = item.split("/") ## Splits each line by slash, to 8 parts...
			found_player = False
			if len(split_string) == 8: ## If we have 8 seperate sections, then it matches our expected layout.
				## Specifially, we're looking for the structure to be like :: /root/BBTCG/assets/<season_name>/<basic_or_shiny>/<team_name>/<player_name>.png or .gif
				found_player = True
				player_name = split_string[7].split(".")[0]
				team_name = split_string[6]
				if split_string[5] == "Basic": 
					shiny = False
				elif split_string[5] == "Shiny": 
					shiny = True
					player_name = "Shiny " + player_name
				season_name = split_string[4]
				image_location = item

			## If we have indeed found a player, add it to the DB
			if found_player == True:
				## Check for if it already exists in the DB first though.
				already_exists = False
				for i in range(len(json_items)):
					if json_items[i]["name"] == player_name: already_exists = True
				## If it doesn't already exist, now we add it in
				if already_exists == False:
					print(f"Populate-database :: Found new player and adding them to database.\n\tName == {player_name}\n\tLocation == {image_location}")
					json_items.append({
						"name": player_name,
						"team_name": team_name,
						"season_name": season_name,
						"image_location": image_location,
						"shiny": shiny,
						"position": "generic",
						"deceased": False,
						"rarity": "common"
					})
		# overwrite, save current data
		json_content["items"] = json_items
		self.overwrite_json(json_content)
		return "success", "success"

	#
	# REMOVE ITEM
	#

	async def remove_item(self, item_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]
		item_found = item_index = 0
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				item_found = 1
				item_index = i
		if not item_found:
			return "error", "Item not found."

		# delete from the "items" section
		json_items.pop(item_index)

		# delete for everyone who had it in their inventory
		user_content = json_content["userdata"]
		for i in range(len(user_content)):
			# tricky
			# i suppose the variable type will either be a string with "none"
			# or a list with lists : ["item_name", amount], so items = [ [], [] ] etc
			if user_content[i]["items"] == "none":
				pass
			else:
				try:
					for ii in range(len(user_content[i]["items"])):
						print(user_content[i]["items"][ii])
						current_name = user_content[i]["items"][ii][0]
						if current_name == item_name:
							user_content[i]["items"].pop(ii)
				except Exception as e:
					print(e)

		# overwrite, end
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# BUY ITEM
	#

	## TODO: would remove, but we should take a look at this for actually giving cards to players
	async def buy_item(self, user, channel, username, user_pfp, item_name, amount, user_roles, server_object,
					   user_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]
		item_found = item_index = 0
		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				item_found = 1
				item_index = i
		if not item_found:
			return "error", "Item not found."
		item = json_items[item_index]
		# get variables
		item_name = item_name
		item_price = item["price"]
		req_roles = item["required_roles"]
		give_roles = item["given_roles"]
		rem_roles = item["removed_roles"]
		max_bal = item["maximum_balance"]
		remaining_stock = item["amount_in_stock"]
		expiration_date = item["expiration_date"]
		reply_message = item["reply_message"]

		# calculate expiration
		today = datetime.today()
		expire = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
		if today > expire:
			return "error", f"Item has already expired. Expiring date was {expiration_date}"
		# else we're good

		# 1. check req roles
		try:
			if req_roles == "none":
				pass
			else:
				for i in range(len(req_roles)):
					if int(req_roles[i]) not in user_roles:
						return "error", f"User does not seem to have all required roles."
		except Exception as e:
			print("1", e)
			return "error", f"Unexpected error."

		### BEFORE update, "check rem roles" and "check give roles" was located here. it seems that
		### the intended usage i had back then was to do that stuff once the item is bought.
		### thus this is now located below, after checking balance etc.

		# 4. check if enough money

		sum_price = item_price * amount
		sum_price = round(sum_price, 0)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]
		user_cash = user_content["cash"]
		if user_cash < sum_price:
			return "error", f"Error! Not enough money in cash to purchase.\nto pay: {sum_price} ; in cash: {user_cash}"

		# 5. check if not too much money
		user_bank = user_content["bank"]
		if max_bal != "none":
			if (user_bank + user_cash) > max_bal:
				return "error", f"Error! You have too much money to purchase.\nnet worth: {'{:,}'.format(int(user_bank + user_cash))} ; max bal: {max_bal}"

		# 6. check if enough in stock or not
		if max_bal != "none":
			if remaining_stock <= 0:
				return "error", f"Error! Item not in stock."
			elif amount > remaining_stock:
				return "error", f"Error! Not enough remaining in stock ({remaining_stock} remaining)."

		# 8. rem money, substract stock, print message, add to inventory
		user_content["cash"] -= sum_price
		try:
			item["amount_in_stock"] -= amount
		except:
			# in this case theres no limit so we dont substract anything
			pass

		if user_content["items"] == "none":
			user_content["items"] = [[item_name, amount]]
		else:
			needAppend = True
			for i_i in range(len(user_content["items"])):
				if user_content["items"][i_i][0] == item_name:
					user_content["items"][i_i][1] += amount
					needAppend = False
					break
			if needAppend:
				user_content["items"].append([item_name, amount])

		# 2. check give roles
		try:
			if rem_roles == "none":
				pass
			else:
				for i in range(len(rem_roles)):
					role = discord.utils.get(server_object.roles, id=int(rem_roles[i]))
					print(role)
					await user_object.remove_roles(role)
		except Exception as e:
			print("2", e)
			return "error", f"Unexpected error."

		# 3. check rem roles
		try:
			if req_roles == "none":
				pass
			else:
				for i in range(len(give_roles)):
					role = discord.utils.get(server_object.roles, id=int(give_roles[i]))
					print(role)
					await user_object.add_roles(role)
		except Exception as e:
			print("3", e)
			return "error", f"Unexpected error."
		color = self.discord_blue_rgb_code
		embed = discord.Embed(
			description=f"You have bought {amount} {item_name} and paid {str(self.currency_symbol)} **{'{:,}'.format(int(sum_price))}**",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text=reply_message)
		await channel.send(embed=embed)

		# overwrite, end
		json_content["userdata"][user_index] = user_content
		json_content["items"] = json_items
		self.overwrite_json(json_content)

		return "success", "success"
	
	#
	# BRONZE SILVER GOLD CARD PACKS
	#

	async def buy_pack(self, user, channel, username, user_pfp, pack_type, user_roles, server_object, user_object):
		if pack_type == "bronze":
			cards_to_draw = 3
			shinys_possible = 1
			shiny_chance = 1
			cost = 100
		elif pack_type == "silver":
			cards_to_draw = 4
			shinys_possible = 1
			shiny_chance = 3
			cost = 175
		elif pack_type == "gold":
			cards_to_draw = 5
			shinys_possible = 2
			shiny_chance = 1
			cost = 300

		## Quickly check if we can afford this...
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]
		user_cash = user_content["cash"]
		if user_cash < cost:
			return "error", f"Error! Not enough money in cash to purchase.\nto pay: {cost} ; in cash: {user_cash}"
		user_content["cash"] -= cost
		user_content["engagement"] += 1
		json_content["userdata"][user_index] = user_content
		self.overwrite_json(json_content)

		## Construct Groupings
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		json_items = json_content["items"]
		shiny_l = []; shiny_r = []; shiny_uc = []; shiny_c = []
		basic_l = []; basic_r = []; basic_uc = []; basic_c = []

		db_size = len(json_items)
		##print(f"Buy-Pack :: Pre-loop, db_size is {db_size}")
		for x in range(db_size):
			if (json_items[x]["shiny"] == True) and (json_items[x]["rarity"] == "common"): shiny_c.append(json_items[x])
			elif (json_items[x]["shiny"] == True) and (json_items[x]["rarity"] == "uncommon"): shiny_uc.append(json_items[x])
			elif (json_items[x]["shiny"] == True) and (json_items[x]["rarity"] == "rare"): shiny_r.append(json_items[x])
			elif (json_items[x]["shiny"] == True) and (json_items[x]["rarity"] == "legendary"): shiny_l.append(json_items[x])
			elif (json_items[x]["shiny"] == False) and (json_items[x]["rarity"] == "common"): basic_c.append(json_items[x])
			elif (json_items[x]["shiny"] == False) and (json_items[x]["rarity"] == "uncommon"): basic_uc.append(json_items[x])
			elif (json_items[x]["shiny"] == False) and (json_items[x]["rarity"] == "rare"): basic_r.append(json_items[x])
			elif (json_items[x]["shiny"] == False) and (json_items[x]["rarity"] == "legendary"): basic_l.append(json_items[x])

		##print(f"Buy-Pack :: Organized db into seperate arrays...")
		while cards_to_draw != 0:
			##print(f"Buy-Pack :: Inside Loop, cards left to draw is == {cards_to_draw}")
			# load json
			json_file = open(self.pathToJson, "r")
			json_content = json.load(json_file)
			json_items = json_content["items"]
			user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
			user_content = json_content["userdata"][user_index]

			# see the odds of shiny
			shiny_get = False
			if (random.randrange(0,100) <= shiny_chance and shinys_possible > 0) or (pack_type == "gold" and cards_to_draw == 5):
				shiny_get = True
				shinys_possible -= 1
			## Perform Card Rarity weighting
			card_rarity_number = random.randrange(0,33) ## range is 0-32 included
			if card_rarity_number <= 2:
				card_rarity_get = "legendary"
				color = discord.Color.from_rgb(245, 126, 34) ## Orange
			elif card_rarity_number >= 3 and card_rarity_number <= 7:
				card_rarity_get = "rare"
				color = discord.Color.from_rgb(35, 85, 222) ## Blue
			elif card_rarity_number >= 8 and card_rarity_number <= 18:
				card_rarity_get = "uncommon"
				color = discord.Color.from_rgb(43, 191, 38) ## Green
			elif card_rarity_number >= 19:
				card_rarity_get = "common"
				color = discord.Color.from_rgb(230, 234, 240) ## White

			##print(f"Buy-Pack :: Card decided, we are getting a == {card_rarity_get} == and is it shiny...{shiny_get}")
			## Time to pull a card snd see if the requirements match our rando numbers
			if (shiny_get == True) and (card_rarity_get == "legendary") :
				draw_pool = shiny_l
			elif (shiny_get == True) and (card_rarity_get == "rare") :
				draw_pool = shiny_r
			elif (shiny_get == True) and (card_rarity_get == "uncommon") :
				draw_pool = shiny_uc
			elif (shiny_get == True) and (card_rarity_get == "common") :
				draw_pool = shiny_c
			elif (shiny_get == False) and (card_rarity_get == "legendary") :
				draw_pool = basic_l
			elif (shiny_get == False) and (card_rarity_get == "rare") :
				draw_pool = basic_r
			elif (shiny_get == False) and (card_rarity_get == "uncommon") :
				draw_pool = basic_uc
			elif (shiny_get == False) and (card_rarity_get == "common") :
				draw_pool = basic_c
			##print(f"Buy-Pack :: Drawing pool has been made, it has entries == " + str(len(draw_pool)))
			pull_number = random.randrange(0,len(draw_pool))
			##print(f"Buy-Pack :: designated pullnumber from randrange [0-" + str(len(draw_pool)) + f"] and we got {pull_number}")
			confirmed_card = draw_pool[pull_number]
			item_name = confirmed_card["name"]
			card_image = confirmed_card["image_location"]

			## Altering the pre/suffix to just be plain, so the name is at least in a seperate box
			rarity_prefix = "```\n"
			rarity_suffix = "\n```"
			description_name = rarity_prefix + item_name + rarity_suffix
			description_rarity = "Rarity :: **" + card_rarity_get + "**"

			## Display card pull
			embed = discord.Embed(description=f"You got a {description_name}\n{description_rarity}", color=color)
			if shiny_get == False: 
				image_to_embed = discord.File(card_image, filename="image.png")
				embed.set_image(url="attachement://image.png")
			if shiny_get == True: 
				image_to_embed = discord.File(card_image, filename="image.gif")
				embed.set_image(url="attachement://image.gif")
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(file=image_to_embed, embed=embed)

			## Add item to inventory
			if user_content["items"] == "none":
				user_content["items"] = [[item_name, 1]]
			else:
				needAppend = True
				for i_i in range(len(user_content["items"])):
					if user_content["items"][i_i][0] == item_name:
						user_content["items"][i_i][1] += 1
						needAppend = False
						break
				if needAppend:
					user_content["items"].append([item_name, 1])

			# overwrite data
			json_content["userdata"][user_index] = user_content
			json_content["items"] = json_items
			self.overwrite_json(json_content)
			cards_to_draw -= 1
			## end loop here
		## end, return
		return "bought pack", "success"

	#
	# GIVE ITEM
	#

	async def give_item(self, user, channel, username, user_pfp, item_name, amount, reception_user, server_object,
						user_object, recept_username):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		reception_user_index, new_data = self.find_index_in_db(json_content["userdata"], reception_user)
		recept_uname = recept_username
		if new_data != "none":
			json_content["userdata"] = new_data

		json_user_content = json_content["userdata"][user_index]
		json_recept_content = json_content["userdata"][reception_user_index]

		try:
			if json_user_content["items"] == "none":
				return "error", f"❌ You do not have any items to give"
			else:
				worked = False
				for ii_i in range(len(json_user_content["items"])):
					if json_user_content["items"][ii_i][0] == item_name:
						if (json_user_content["items"][ii_i][1] - amount) < 0:
							return "error", f"❌ You do not have enough items of that item to give."
						json_user_content["items"][ii_i][1] -= amount
						worked = True
						
						## Check for anything that is now empty
						if json_user_content["items"][ii_i][1] == 0:
							user_items = json_user_content["items"]
							nil_list = []
							for i in range(len(user_items)):
								if user_items[i][1] == 0: ## check which items are at value 0 and add to a list
									nil_list.append(user_items[i])
							for x in range(len(nil_list)):
								user_items.remove(nil_list[x]) ## Remove matching instances of the list from inventory
							json_user_content["items"] = user_items

						break
				if worked == False:
					return "error", f"❌ You do not have that item to give"

			# so we should be good, now handling the reception side
			if json_recept_content["items"] == "none":
				json_recept_content["items"] = [[item_name, amount]]
			else:
				needAppend = True
				for i_i in range(len(json_recept_content["items"])):
					if json_recept_content["items"][i_i][0] == item_name:
						json_recept_content["items"][i_i][1] += amount
						needAppend = False
						break
				if needAppend:
					json_recept_content["items"].append([item_name, amount])

		except:
			return "error", f"❌"

		# inform user
		color = self.discord_success_rgb_code
		embed = discord.Embed(
			description=f"✅ {recept_uname.mention} has received {'{:,}'.format(int(amount))} {item_name} from you!",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		json_user_content["engagement"] += 4
		json_content["userdata"][user_index] = json_user_content
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# CHECK INVENTORY
	#

	## TODO: Would like to order the inventory
	## TODO: Also need to add other options to this, for going to html page...
	async def check_inventory(self, user, channel, username, user_pfp, display_mode):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]
		item_content = json_content["items"]

		items = user_content["items"]

		## First we wanna remove nil items:
		nil_list = []
		for i in range(len(items)):
			if items[i][1] == 0: ## check which items are at value 0 and add to a list
				nil_list.append(items[i])
		for x in range(len(nil_list)):
			items.remove(nil_list[x]) ## Remove matching instances of the list from inventory

		## Construct a team list, and seperate count, as well as a rarity list and count
		team_list = []
		for i in range(len(item_content)):
			team_list.append(item_content[i]["team_name"])
		team_list = list(dict.fromkeys(team_list))
		team_count = []
		for i in range(len(team_list)): team_count.append(0)
		rarity_list = ["common", "uncommon", "rare", "legendary"]
		rarity_count = [0, 0, 0, 0]

		if items == "none":
			inventory_checkup = "**Inventory empty. No items owned.**"
		else:
			inventory_checkup = ""
			if display_mode == "default": ## Default shows individual card counts
				for i in range(len(items)):
					rarity = "?"
					team_name = "?"
					## This lil loop gets matchign stats of items...
					for ii in range(len(item_content)):
						if items[i][0] == item_content[ii]["name"]: 
							rarity = item_content[ii]["rarity"]
							team_name = item_content[ii]["team_name"]
					## Count teams and rarity here
					if team_name in team_list: team_count[team_list.index(team_name)] += 1
					if rarity in rarity_list: rarity_count[rarity_list.index(rarity)] += 1

					## Below is interesting, we want to align parts of the writing to make it more uniform, so we count characters and decide how many tabs we need.
					number_of_tabs = (7-(len(items[i][0])//4))
					number_of_extra_spaces = (3-(len(items[i][0])%4))
					tab_string = ""
					for iii in range(number_of_tabs): tab_string +="\t"
					for iii in range(number_of_extra_spaces): tab_string +=" "
					inventory_checkup += f"`{items[i][1]} :: {items[i][0]} {tab_string}== Rarity: {rarity}`\n"
					
			elif display_mode == "teams": 
				for i in range(len(items)): ## teams show players belonging to teams
					team_name = "?"
					## This lil loop gets matchign stats of items...
					for ii in range(len(item_content)):
						if items[i][0] == item_content[ii]["name"]: 
							team_name = item_content[ii]["team_name"]
					## Count teams and rarity here
					if team_name in team_list: team_count[team_list.index(team_name)] += 1
				for i in range(len(team_list)):
					inventory_checkup += f"`{team_count[i]} :: {team_list[i]}`\n"
			elif display_mode == "rarity":
				for i in range(len(items)): ## rarity shows number per rarity
					rarity = "?"
					## This lil loop gets matchign stats of items...
					for ii in range(len(item_content)):
						if items[i][0] == item_content[ii]["name"]: 
							rarity = item_content[ii]["rarity"]
					## Count teams and rarity here
					if rarity in rarity_list: rarity_count[rarity_list.index(rarity)] += 1
				for i in range(len(rarity_list)):
					inventory_checkup += f"`{rarity_count[i]} :: {rarity_list[i]}`\n"

		color = self.discord_blue_rgb_code
		embed = discord.Embed(title="Owned Items", description=f"{inventory_checkup}", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		# overwrite, end
		# not needed

		return "success", "success"

	
	async def display_card(self, user, channel, username, user_pfp, item_name):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)
		json_items = json_content["items"]
		found_card = False

		if item_name == "random": ## Pull a random card from the user's inventory
			user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
			user_content = json_content["userdata"][user_index]
			user_items = user_content["items"]
			item_position = random.randrange(0,len(user_items))
			item_name = user_items[item_position][0]

		for cards in json_items: ## Find the card we're looking for from the inventory
			if cards["name"] == item_name:
				image_to_show = cards["image_location"]
				team_name = cards["team_name"]
				rarity_to_show = cards["rarity"]
				shiny_card = cards["shiny"]
				found_card = True
				break

		if found_card == False:
			return "error", "can't find card to display"
			
		if rarity_to_show == "legendary": color = discord.Color.from_rgb(245, 126, 34) ## Orange
		elif rarity_to_show == "rare": color = discord.Color.from_rgb(35, 85, 222) ## Blue
		elif rarity_to_show == "uncommon": color = discord.Color.from_rgb(43, 191, 38) ## Green
		elif rarity_to_show == "common": color = discord.Color.from_rgb(230, 234, 240) ## White

		embed = discord.Embed(description=f"{item_name}, of {team_name}.\n  Rarity: {rarity_to_show}", color=color)
		if shiny_card:			
			file_to_embed = discord.File(image_to_show, filename="image.gif")
			embed.set_image(url="attachment://image.gif")
		else:
			file_to_embed = discord.File(image_to_show, filename="image.png")
			embed.set_image(url="attachment://image.png")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(file=file_to_embed, embed=embed)
		return "success", "success"

	#
	# ROLE INCOMES - NEW ONE
	#

	async def new_income_role(self, user, channel, username, user_pfp, income_role_id, income):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		for i in range(len(json_income_roles)):
			if json_income_roles[i]["role_id"] == income_role_id:
				return "error", "Role already exists as income role."

		now = str(datetime.now())
		json_income_roles.append({
			"role_id": income_role_id,
			"role_income": income,
			"last_updated": now
		})
		color = self.discord_blue_rgb_code
		embed = discord.Embed(
			description=f"New income role added.\nrole_id : {income_role_id}, income : {str(self.currency_symbol)} **{'{:,}'.format(int(income))}**",
			color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text="smooth")
		await channel.send(embed=embed)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROLE INCOMES - REMOVE ONE
	#

	async def remove_income_role(self, user, channel, username, user_pfp, income_role_id):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]
		role_found = role_index = 0
		for i in range(len(json_income_roles)):
			if json_income_roles[i]["role_id"] == income_role_id:
				role_found = 1
				role_index = i
		if not role_found:
			return "error", "Role not found."

		# delete from the "items" section
		json_income_roles.pop(role_index)

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# ROLE INCOMES - LIST
	#

	async def list_income_roles(self, user, channel, username, user_pfp, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]

		role_list_report = f"__Income Roles List:__\n\n"

		for i in range(len(json_income_roles)):
			role = discord.utils.get(server_object.roles, id=int(json_income_roles[i]["role_id"]))
			ping_role = f"<@&{json_income_roles[i]['role_id']}>"

			role_list_report += f"Role name: "+str(ping_role)+"\n" \
								f"Role income: {self.currency_symbol} {'{:,}'.format(json_income_roles[i]['role_income'])}\n\n"

		role_list_report += "---------------------------------"

		await channel.send(role_list_report, silent=True)

		# overwrite, end
		# not needed

		return "success", "success"

	#
	# ROLE INCOMES - UPDATE INCOMES
	#
	# okay were gonna change it to an hourly income (10.06.2023)

	async def update_incomes(self, user, channel, username, user_pfp, server_object):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_income_roles = json_content["income_roles"]
		user_content = json_content["userdata"]

		# pretty straight forward i think.
		# first, we go into each role object
		# then we check in everyones roles if they have the role

		for role_index in range(len(json_income_roles)):
			role_id = json_income_roles[role_index]["role_id"]

			# new edit for hourly income:
			now = datetime.now()
			last_income_update_string = json_income_roles[role_index]["last_updated"]
			# get a timeobject from the string
			last_income_update = datetime.strptime(last_income_update_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_income_update
			passed_time_hours = passed_time.total_seconds() // 3600.0

			## TODO: For now, just Coaches as a role, but i'll need to modify this for other roles eventually.
			role = discord.utils.find(lambda r: r.name == "Coaches", server_object.roles)	
			for member in role.members:
				try:
					if passed_time_hours >= 1:
						# also to create user in case he isnt registered yet
						user_index, new_data = self.find_index_in_db(json_content["userdata"], member.id)

						json_user_content = json_content["userdata"][user_index]
						json_income_roles[role_index]["last_updated"] = str(now)
						payment = json_income_roles[role_index]["role_income"] * int(passed_time_hours)
						bonus_engagement = json_user_content["engagement"]
						json_user_content["engagement"] // 2
						json_user_content["cash"] += (payment + bonus_engagement)
						# overwrite
						json_content["userdata"][user_index] = json_user_content
				except:
					pass

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"
