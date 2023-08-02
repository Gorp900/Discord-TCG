import json, os, time, random, math, sys, discord, math
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
		self.pathToJson = "database/database.json"
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
		print(data_to_search)
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
		data_to_search.append({
			"user_id": user_to_find,
			"cash": 0,
			"engagement": 0,
			# "balance" : cash + bank
			# "roles": "None" ; will be checked when calculating weekly auto-role-income
			"items": "none",
		})
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

	## TODO: Need to edit what we're going to need to create an item
	async def create_new_item(self, item_name, cost, description, duration, stock, roles_id_required, roles_id_to_give,
							  roles_id_to_remove, max_bal, reply_message):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		json_items = json_content["items"]

		for i in range(len(json_items)):
			if json_items[i]["name"] == item_name:
				return "error", "Item with such name already exists."

		# calculate item duration
		today = datetime.today()
		print(today)
		expiration_date = today + timedelta(days=duration)

		print("expiration date : ", expiration_date)

		## TODO: Item Vars
		json_items.append({
			"name": item_name,
			"price": cost,
			"description": description,
			"duration": duration,
			"amount_in_stock": stock,
			"required_roles": roles_id_required,
			"given_roles": roles_id_to_give,
			"removed_roles": roles_id_to_remove,
			"maximum_balance": max_bal,
			"reply_message": reply_message,
			"expiration_date": str(expiration_date)
		})

		# overwrite, end
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

	async def bronze_pack(self, user, channel, username, user_pfp, user_roles, server_object, user_object):
		
		for x in range(3): ## 3 card pulls...
			# load json
			json_file = open(self.pathToJson, "r")
			json_content = json.load(json_file)
			json_items = json_content["items"]
			user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
			user_content = json_content["userdata"][user_index]
			
			# see the odds of shiney
			if random.randrange(0,100) >= 95: ## 5% chance
				shiney_get = True
			else: shiney_get = False

			## TODO: Need to redo the random number based on whether we should be getting a shiney or not
			## 	Possibly just use a while (not confirmed_card) ...
			pull_number = random.randrange(0,len(json_items))
			if json_items[pull_number]["shiney"] == True :
				if shiney_get:
					confirmed_card = json_items[pull_number]
				else:
					confirmed_card = json_items[pull_number+1]
			else:
				if shiney_get:
					confirmed_card = json_items[pull_number]
				else:
					confirmed_card = json_items[pull_number+1]
			# get item name and card_image
			item_name = confirmed_card["name"]
			card_image = confirmed_card["image_url"]

			## Display card pull
			color = self.discord_green_rgb_code
			embed = discord.Embed(description=f"You found a {item_name} ", color=color)
			embed.set_image(url=card_image)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
	
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
			## end loop here
		## end, return
		return "bought bronze pack", "success"
	
	async def silver_pack(self, user, channel, username, user_pfp, user_roles, server_object, user_object):
		return "bought silver pack", "success"
	
	async def gold_pack(self, user, channel, username, user_pfp, user_roles, server_object, user_object):
		return "bought gold pack", "success"

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
		json_content["userdata"][user_index] = json_user_content
		json_content["userdata"][reception_user_index] = json_recept_content
		self.overwrite_json(json_content)

		return "success", "success"

	#
	# CHECK INVENTORY
	#

	async def check_inventory(self, user, channel, username, user_pfp):
		# load json
		json_file = open(self.pathToJson, "r")
		json_content = json.load(json_file)

		user_index, new_data = self.find_index_in_db(json_content["userdata"], user)
		user_content = json_content["userdata"][user_index]

		items = user_content["items"]
		if items == "none":
			inventory_checkup = "**Inventory empty. No items owned.**"
		else:
			inventory_checkup = ""
			for i in range(len(items)):
				inventory_checkup += f"`{items[i][0]}`; amount: `{items[i][1]}`\n"

		color = self.discord_blue_rgb_code
		embed = discord.Embed(title="Owned Items", description=f"{inventory_checkup}", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		embed.set_footer(text="nice")
		await channel.send(embed=embed)

		# overwrite, end
		# not needed

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

			role_list_report += f"Role name: {ping_role}\n" \
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
			print("p1")
			last_income_update_string = json_income_roles[role_index]["last_updated"]
			print("p2")
			# get a timeobject from the string
			last_income_update = datetime.strptime(last_income_update_string, '%Y-%m-%d %H:%M:%S.%f')
			# calculate difference, see if it works
			passed_time = now - last_income_update
			passed_time_hours = passed_time.total_seconds() // 3600.0

			role = discord.utils.get(server_object.roles, id=int(role_id))
			for member in role.members:
				try:
					# also to create user in case he isnt registered yet
					user_index, new_data = self.find_index_in_db(json_content["userdata"], member.id)

					json_user_content = json_content["userdata"][user_index]
					json_income_roles[role_index]["last_updated"] = str(now)
					json_user_content["cash"] += (json_income_roles[role_index]["role_income"] * int(passed_time_hours))
					# overwrite
					json_content["userdata"][user_index] = json_user_content

				except:
					pass

		# overwrite, end
		json_content["income_roles"] = json_income_roles
		self.overwrite_json(json_content)

		return "success", "success"
