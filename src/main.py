
# --------- Info and general informations -----------

"""
INFO
  Official Repo: https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot

	This is a discord bot written in python, designed to copy some of Unbelievaboat's functions,
	  but add custom stuff to it (e.g no balance limit, automatic balance increase etc)

	The Discord things are from the discord API (import discord)

	the databses are stored in database/ and handled by database/__init__.py
	  that name is chosen to make it something easily importable

	some of these functions and methods are based on another Bot i made, https://github.com/NoNameSpecified/selenor
"""

# --------- BOT CODE BELOW -----------



"""

// INIT

"""

# imports
import discord
import random
from discord.ext.commands import Bot
# custom database handler
import database
from time import sleep


# init discord stuff and json handling
BOT_PREFIX = ("/")  # tupple in case we'd need multiple
token_file = open("/root/BBTCG/PROD/Discord-TCG/src/bot_token", "r")
token = token_file.readline()
#token = "" # Return to zero when committing...
# emojis
emoji_worked = "✅"
emoji_error = "❌"
discord_error_rgb_code = discord.Color.from_rgb(239, 83, 80)
discord_success_rgb_code = discord.Color.from_rgb(83, 239, 80)
intents = discord.Intents.all()
client = Bot(command_prefix=BOT_PREFIX, intents=intents)  # init bot
db_handler = database.pythonboat_database_handler(client)  # ("database.json")


"""

// GLOBAL FUNCTIONS

"""

async def get_user_input(message):
	print("Awaiting User Entry")
	# we want an answer from the guy who wants to give an answer
	answer = await client.wait_for("message", check=lambda response: response.author == message.author and response.channel == message.channel)
	answer = answer.content
	# clean input
	answer = answer.lower().strip() ## GORP:TODO: Do we remove lower() here?

	return answer


async def send_embed(title, description, channel, color="default"):
	# some default colors
	colors = [0xe03ca5, 0xdd7b28, 0x60c842, 0x8ae1c2, 0x008c5a, 0xc5bcc5]
	if color == "default": color = 0xe03ca5
	# create the embed
	embed = discord.Embed(title=title, description=description, color=color)
	await channel.send(embed=embed)
	return


async def send_error(channel):
	embed = discord.Embed(title="Error.", description="Internal Error, call admin.", color=0xff0000)
	await channel.send(embed=embed)
	return


# ~~~ set custom status ~~~
@client.event
async def on_ready():
	activity = discord.Game(name=f"Blood Bowl! Use me with \"{BOT_PREFIX}\"")
	await client.change_presence(status=discord.Status.online, activity=activity)
	# log_channel = 807057317396217947 # in your server, select a channel you want log info to be sent to
									# rightclick and copy id. put the id here. it should look like this : 807057317396217947
	"""
	NEED LOG CHANNEL ID
	"""
	# channel = client.get_channel(log_channel)
	# await channel.send("running")


	# check json, putting it here because has to be in a async function
	check_status = await db_handler.check_json()

	if check_status == "error":
		# channel = client.get_channel(log_channel)
		color = discord_error_rgb_code
		embed = discord.Embed(description=f"Critical error. JSON file is corrupted or has missing variables.\n\n"
										# f"`Error` code : {error_info}`\n" # -- Possibly to add
										  f" Please contact an admin or delete the JSON database, but do a backup before -\n"
										  f"this will result in re-creating the default config but will also **delete all user data**\n\n", color=color)
		embed.set_author(name="UnbelievaBoat-Python Bot", icon_url="https://blog.learningtree.com/wp-content/uploads/2017/01/error-handling.jpg")
		embed.set_footer(text="tip: default config at https://github.com/NoNameSpecified/UnbelievaBoat-Python-Bot")
		# await channel.send(embed=embed)
		quit()

	db_handler.get_currency_symbol()

"""

USER-BOT INTERACTION

"""
@client.event
async def on_message(message):

	"""
	start general variable definition
	"""

	# check if message is for our bot
	if not ( message.content.startswith(BOT_PREFIX) ) : 
		## db_handler.non_command_engagement_boost(message.author.id) ## TODO: Need to handle this, but since this check comes so early, what if a coach is new?  How to track last message?
		return 0;

	# prefix checked, we can continue
	usedPrefix = message.content[0] # in case we would add more prefixes later
	# in selenor bot : check for case sensitive or not c.s. commands, not needed for this bot,
	# make it a clean input
	command = message.content.split(usedPrefix)[1].split(" ")

	# stop if not meant for bot. (like just a "?")
	if command[0] in ["", " "]: return 0;

	"""
	basically, if the command is :
		+give money blabla
		we take what is after the prefix and before everything else, to just get the command
		in this case : "give"
		edit : for now we just splitted it, pure command will be taken with command = command[0]
	this is to redirect the command to further handling
	"""
	print(command) # for testing purposes

	param_index = 1
	param = ["none", "none", "none", "none"]
	command_updated = []
	# lets say our command says "remove-item <your mom>"

	try:
		for test_cmd in range(len(command)):
			if command[test_cmd].startswith('"') or command[test_cmd].startswith("'"):
				new_slide = ""
				temp_cmd = test_cmd
				while not(command[temp_cmd].endswith('"') or command[temp_cmd].endswith("'")):
					new_slide += command[temp_cmd] + " "
					temp_cmd += 1
				new_slide += command[temp_cmd]
				command_updated.append(new_slide[1:len(new_slide)-1])
				break
			else:
				command_updated.append(command[test_cmd])
	except:
			await message.channel.send("Error. You maybe opened a single/doublequote or a < and didnt close it")
	command = command_updated
	print(command)
	for param_index in range(len(command)):
		param[param_index] = command[param_index]
	print(f"Command called with parameters : {param}")
	# for use of parameters later on, will have to start at 0, not 1

	# ~~~~ GET DISCORD VARIABLES for use later on
	# to directly answer in the channel the user called in
	channel = message.channel
	server = message.guild
	user = message.author.id
	user_mention = message.author.mention
	if message.author.avatar: user_pfp = message.author.avatar.url
	else: user_pfp = "https://nufflezone.com/wp-content/uploads/2023/05/Icono_Nuffle_Zone_Ball_Black-3000x3000-1-300x300.png"
	username = str(message.author)
	nickname = str(message.author.display_name)
	user_roles = ""
	is_a_bot = False
	## We check if there is a "roles" I beleive this is tied to the bot reading messages of other bots...
	## TODO: this bit doesn't quite work, revert the logic here to just be like 2 lines from here, making user_roles.
	if message.author.roles:
		user_roles = [randomvar.name.lower() for randomvar in message.author.roles]
	else: 
		user_roles = "botmaster"
		is_a_bot = True


	# some stuff will be only for staff, which will be recognizable by the botmaster role
	## NOTE: Put the botmaster roles as lower_case for safety
	staff_request = 0
	botmaster_roles = ["botmaster", "manager", "commissioners"]
	for role in user_roles:
		for bt_role in botmaster_roles:
			if role == bt_role: staff_request = 1
			break
	#staff_request = 1 if (("Manager" in user_roles) or ("Commissioners" in user_roles)) else 0 ## TODO: Rename botmaster role?
	print("staff status : ", staff_request)
	command = command[0]

	#

	"""
	START PROCESSING COMMANDS
	"""

	"""

	possible improvements : everything in int, not float
							all displayed numbers with "," as thousands operator
							people can enter amounts with thousands operator
	"""

	"""
		REGULAR COMMANDS (not staff only)
	"""
	# list of commands # their aliases, to make the help section easier
	all_reg_commands_aliases = {
		"gorptest": "",
		"bronze-pack": "bp",
		"silver-pack": "sp",
		"gold-pack": "gp",
		"balance": "bal",
		"give": "pay",
		"leaderboard": "lb",
		"help": "info",
		"module": "moduleinfo"
	}
	all_reg_commands = list(all_reg_commands_aliases.keys())


	### BOT-MANAGED Update Income
	## The ONLY command a bot should be doing is this one... it's basically a duplicate of the main "update-income"
	if is_a_bot:
		if command in ["update-income"]:
			try:
				status, update_incomes_return = await db_handler.update_incomes(user, channel, username, user_pfp, server)
				if status == "error":
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{update_incomes_return}", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except Exception as e:
				print(e)
				await send_error(channel)
			print(f"BOT AUTO UPDATE INCOME COMPLETE")
			return
		return

	# --------------
	#    BALANCE
	# --------------

	if command in ["balance", all_reg_commands_aliases["balance"]]:
		# you can either check your own balance or someone else's bal
		if "none" in param[1]:
			# tell handler to check bal of this user
			userbal_to_check = user
			username_to_check = username
			userpfp_to_check = user_pfp
		# only one user to check, so only 1 param, if 2 -> error
		elif param[1] != "none" and param[2] != "none":
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `[user]` argument given.\n\nUsage:\n`balance <user>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		# else we want the balance of someone else
		else:
			userbal_to_check = str(param[1])  # the mention in channel gives us <@!USERID> OR <@USERIRD>
			if len(userbal_to_check) == 22:
				flex_start = 3
			else: # if len(userbal_to_check) == 21:
				flex_start = 2
			userbal_to_check = "".join(list(userbal_to_check)[flex_start:-1])  # gives us only ID
			try:
				user_fetch = client.get_user(int(userbal_to_check))
				print("hello ?")
				username_to_check = user_fetch
				userpfp_to_check = user_fetch.avatar
			except:
				# we didnt find him
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `[user]` argument given.\n\nUsage:\n`balance <user>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# go through the handler
		try:
			await db_handler.balance(user, channel, userbal_to_check, username_to_check, userpfp_to_check)
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	# 	  GIVE
	# --------------

	elif command in ["give", all_reg_commands_aliases["give"]]:
		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give <member> <amount or all>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = str(param[1])  # the mention in channel gives us <@!USERID> OR <@USERIRD>
		if len(reception_user) == 22:
			flex_start = 3
		else:  # if len(userbal_to_check) == 21:
			flex_start = 2
		reception_user = "".join(list(reception_user)[flex_start:-1])  # gives us only ID
		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

			if int(reception_user) == user:
				# cannot send money to yourself
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  You cannot trade money with yourself. That would be pointless.\n"
												  f"(You may be looking for the `add-money` command.)", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`give <member> <amount or all>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		# either all or an amount, not some random string
		if amount != "all":
			try:
				# they can use the thousands separator comma
				newAmount = []
				for char in amount:
					if char != ",":
						newAmount.append(char)
				amount = "".join(newAmount)
				amount = int(amount)
				if amount < 1:
					color = discord_error_rgb_code
					embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`give <member> <amount or all>`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount or all>` argument given.\n\nUsage:\n`give <member> <amount or all>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		# handler

		try:
			amount = str(amount)
			status, give_return = await db_handler.give(user, channel, username, user_pfp, reception_user, amount, reception_user_name)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{give_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#  LEADERBOARD
	# --------------

	##TODO: Expand leaderboard! 
	elif command in ["leaderboard", all_reg_commands_aliases["leaderboard"]]:
		return ## Do a quick return since wwe dont want to do this just yet
		modes = ["-cash", "-bank", "-total"]
		page_number = 1
		mode_type = modes[2]
		server_name = server.name
		full_name = server_name  # + mode_type

		# first, vanilla
		if "none" in param[1] and "none" in param[2]:
			# using default vars
			page_number = 1
			mode_type = modes[2]
			full_name += " Leaderboard"
		# one argument
		elif param[1] != "none" and "none" in param[2]:
			if param[1] in modes:
				mode_type = param[1]
				page_number = 1
				if mode_type == "-total": full_name += " Leaderboard"
				if mode_type == "-cash": full_name += " Cash Leaderboard"
				if mode_type == "-bank": full_name += " Bank Leaderboard"
			else:
				try:
					page_number = int(param[1])
					mode_type = modes[2]
					full_name += " Leaderboard"
				except:
					color = discord_error_rgb_code
					embed = discord.Embed(
						description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
									f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
		# two arguments
		else:
			try:
				page_number = int(param[1])
				mode_type = param[2]
				if mode_type == "-total": full_name += " Leaderboard"
				elif mode_type == "-cash": full_name += " Cash Leaderboard"
				elif mode_type == "-bank": full_name += " Bank Leaderboard"
				else:
					color = discord_error_rgb_code
					embed = discord.Embed(
						description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
									f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
					embed.set_author(name=username, icon_url=user_pfp)
					await channel.send(embed=embed)
					return
			except:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `[-cash | -bank | -total]` argument given.\n\nUsage:\n"
								f"`leaderboard [page] [-cash | -bank | -total]`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		print(f"Looking for {full_name}, at page {page_number}, in mode {mode_type}")

		# handler

		try:
			status, lb_return = await db_handler.leaderboard(user, channel, username, full_name, page_number, mode_type, client)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{lb_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
	
	# --------------
	#     HELP
	# --------------

	elif command in ["help", all_reg_commands_aliases["help"]]:
		color = discord.Color.from_rgb(3, 169, 244)
		embed = discord.Embed(title=f"Help System", color=color)
		embed.add_field(name="balance", value=f"Usage: `/balance`\nShows you're current balance of cyans", inline=False)
		embed.add_field(name="inventory", value=f"Usage: `/inventory <type>`\nShows your currently collected cards and other info.  Type can be [default, teams, rarity].  Leaving it blank is [default]", inline=False)
		## embed.add_field(name="leaderboard", value=f"Usage: `/leaderboard`\nShows who has the most cyans", inline=False) ## TODO: Re-implement when autocomplete is in
		embed.add_field(name="show-card", value=f"Usage: `/show-card \"<card_name>\"`\nShows the named card to the chat.  If no card is named, it shows a random card from your inventory", inline=False)
		embed.add_field(name="give", value=f"Usage: `/give <user> <amount>`\nSends <amount> of cyans to <user> pinged", inline=False)
		embed.add_field(name="give-item", value=f"Usage: `/give-item <user> <item> <amount>`\nSends <item> to <user> pinged.  If <amount> is left blank, it sends a single item", inline=False)
		embed.add_field(name="bronze-pack", value=f"Usage: `/bronze-pack` OR `/bp` \nPurchases a Bronze Pack of cards for 100 Coins", inline=False)
		embed.add_field(name="silver-pack", value=f"Usage: `/silver-pack` OR `/sp` \nPurchases a Silver Pack of cards for 175 Coins", inline=False)
		embed.add_field(name="gold-pack", value=f"Usage: `/gold-pack` OR `/gp` \nPurchases a Gold Pack of cards for 300 Coins", inline=False)
		# edit stuff
		embed.set_footer(text="For more info, contact an admin")
		await channel.send(embed=embed)
		if(message.content.startswith("/")):
			await message.delete()

		if not staff_request: return
		#### in 2 parts because one was too long

		embed = discord.Embed(title=f"Help System", color=color)
		embed.add_field(name="----------------------\n\nSTAFF ONLY", value=f"requires <botmaster> role", inline=False)
		embed.add_field(name="add-money", value=f"Usage: `add-money <member> <amount>`", inline=False)
		embed.add_field(name="remove-money", value=f"Usage: `remove-money <member> <amount>`", inline=False)
		embed.add_field(name="change-currency", value=f"Usage: `change-currency <new emoji name>`", inline=False)
		embed.add_field(name="----------------------\n\nITEM HANDLING", value=f"create and delete requires <botmaster> role", inline=False)
		embed.add_field(name="create-item", value=f"Usage: `create-item`", inline=False)
		embed.add_field(name="delete-item", value=f"Usage: `delete-item <item name>`", inline=False)
		embed.add_field(name="populate-database", value=f"Usage: `populate-database` :: Updates database by actual saved files on host machine", inline=False)
		embed.add_field(name="----------------------\n\nINCOME ROLES", value=f"create, delete and update requires <botmaster> role", inline=False)
		embed.add_field(name="add-income-role", value=f"Usage: `add-income-role <role pinged> <income>`", inline=False)
		embed.add_field(name="remove-income-role", value=f"Usage: `remove-income-role <role pinged>`", inline=False)
		embed.add_field(name="list-roles", value=f"Usage: `list-roles`", inline=False)
		embed.add_field(name="update-income", value=f"Usage: `update-income` | Will gift everyone cyans based on role |\nshould be run every hour or so, or at least every day", inline=False)
		await channel.send(embed=embed)

		## Notes to GORP:
		# enagagement is awarded for buying packs, giving away cash, and giving away cards (ie: trading)
		#    engagement is used to boost the amount of cash you receive from update-income
		#    There is work to be done to include other ways to reward engagement


	# --------------
	#  MODULE INFO
	# --------------

	## TODO: What does the module command really even do?  Add and removed additional python games i guess?
	elif command in ["module", all_reg_commands_aliases["module"]]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		if "none" in param[1] or param[2] != "none":  # we need 1 and only 1 parameter
			color = discord_error_rgb_code
			embed = discord.Embed(
				description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`module <module>`",
				color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		module = param[1]

		# handler

		try:
			status, module_return = await db_handler.module(user, channel, module)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{module_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		"""
			STAFF COMMANDS
		"""

	# --------------
	#   ADD-MONEY
	# --------------

	elif command == "add-money":
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = str(param[1])  # the mention in channel gives us <@!USERID> OR <@USERIRD>
		if len(reception_user) == 22:
			flex_start = 3
		else:  # if len(userbal_to_check) == 21:
			flex_start = 2
		reception_user = "".join(list(reception_user)[flex_start:-1])  # gives us only ID
		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		try:
			# they can use the thousands separator comma
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-money <member> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			amount = str(amount)
			status, add_money_return = await db_handler.add_money(user, channel, username, user_pfp, reception_user, amount, reception_user_name)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{add_money_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#  REMOVE-MONEY
	# --------------

	elif command == "remove-money":
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 2 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of both parameters

		# CHECK 1

		reception_user = str(param[1])  # the mention in channel gives us <@!USERID> OR <@USERIRD>
		if len(reception_user) == 22:
			flex_start = 3
		else:  # if len(userbal_to_check) == 21:
			flex_start = 2
		reception_user = "".join(list(reception_user)[flex_start:-1])  # gives us only ID
		try:
			user_fetch = client.get_user(int(reception_user))
			print(user_fetch)
			reception_user_name = user_fetch

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`remove-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# CHECK 2

		amount = param[2]
		try:
			# they can use the thousands separator comma
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money <member> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`remove-money <member> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			amount = str(amount)
			status, rm_money_return = await db_handler.remove_money(user, channel, username, user_pfp, reception_user, amount, reception_user_name)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{rm_money_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# --------------
	#   EDIT VARS
	# --------------

	elif command in ["change", "edit"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2] or "none" in param[3]:  # we need 3 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`change <module> <variable> <new value>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# that would end up messing everything up
		if param[2] == "name":
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  You cannot change module names.", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# we need to check validity of new value parameter
		# other checks will be done in the handler

		# CHECK
		module_name = param[1]
		variable_name = param[2]
		new_value = param[3]
		try:
			new_value = int(new_value)
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<new value>` argument given.\n\nUsage:\n`change <module> <variable> <new value>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			new_value = str(new_value)
			status, edit_return = await db_handler.edit_variables(user, channel, username, user_pfp, module_name, variable_name, new_value)

			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{edit_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------
	#   CHANGE CURRENCY SYMBOL
	# ---------------------------

	elif command in ["change-currency", "edit_currency"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`change-currency <new emoji name>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		new_emoji_name = param[1]

		# handler

		try:
			status, emoji_edit_return = await db_handler.change_currency_symbol(user, channel, username, user_pfp, new_emoji_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_edit_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)


		"""
			SPECIAL COMMANDS
		"""

		"""
		TODO :
			catalog
			add all these to the help menu
			use-item
		"""

	#### GorpTest is a testing command for various things at the time of running...
	elif command in ["gorptest"]:
		if not staff_request:
			return
		test_text = "DOUGAL!"
		embed = discord.Embed(title="MY_TITLE", description=f"Here's ```arm\n{test_text}\n``` card", color=discord_success_rgb_code)
		test_image = "/root/BBTCG/assets/Season 16/Basic/Shoddy Workmanship/Dougal.png"
		file_to_embed = discord.File(test_image, filename="image.png")
		embed.set_image(url="attachment://image.png")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(file=file_to_embed, embed=embed)

		##ret_status = await db_handler.non_command_engagement_boost(user)
		return
	
	#### This command is set to automatically deal with our databse to avoid needing manual writing
	####      At least for most of it, some manual intervention is still needed for some parts
	elif command in ["populate-database"]:
		if not staff_request:
			return
		ret_status = await db_handler.populate_database()
		return

	# ---------------------------
	#   Show Card!
	# ---------------------------

	elif command in ["show-card"]:
		if "none" in param[1]:  # If no item name: random card!
			item_name = "random"
		else: item_name = param[1]
		try:
			status, showcard_return = await db_handler.display_card(user, channel, username, user_pfp, item_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{showcard_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   Find Card
	# ---------------------------

	elif command in ["find-item"]:
		if "none" in param[1]:  
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  No card to find", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		else: item_name = param[1]
		try:
			userList = []
			outputList = []
			status = await db_handler.find_item(userList, item_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{status}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
			
			for i in range(len(userList)):
				user = (await client.fetch_user(userList[i]))
				outputList.append(user.global_name)

			outputList = '\n'.join(outputList)
			color = discord.Color.from_rgb(3, 169, 244)
			embed = discord.Embed(description=f"Find-Item", color=color)
			embed.add_field(name = "Users who own card:", value = outputList)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
		
		except Exception as e:
			print(e)
			await send_error(channel)
		
	# ---------------------------
	#   ITEM CREATION
	# ---------------------------

	elif command in ["create-item", "new-item", "item-create"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		currently_creating_item = True
		checkpoints = 1
		last_report = ""
		color = discord.Color.from_rgb(3, 169, 244)
		# send a first input which we will then edit
		info_text = ":one: What should the new item be called?\nThis name should be unique and no more than 200 characters."
		first_embed = discord.Embed(title="Item Info", description="Name\n.", color=color)
		first_embed.set_footer(text="Type cancel to quit")
		await channel.send(info_text, embed=first_embed)

		while currently_creating_item:
			user_input = ""
			# get input first
			user_input = await get_user_input(message)
			print(user_input)
			# check if user wants cancel
			if user_input == "cancel":
				await channel.send(f"{emoji_error}  Cancelled command.")
				return


			if checkpoints == 1:
				# check 1: name
				if len(user_input) > 200:
					await channel.send(f"{emoji_error} The maximum length for an items name is 200 characters. Please try again.")
					continue
				elif len(user_input) < 3:
					await channel.send(f"{emoji_error}  The minimum length for an items name is 3 characters. Please try again.")
					continue
				# good input
				item_name = user_input
				first_embed = discord.Embed(title="Item Info", color=color)
				first_embed.add_field(name="name", value=f"{item_name}")
				first_embed.set_footer(text="Type cancel to quit")
				next_info = ":two: What Team does this player belong to?"
				last_report = await channel.send(next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 2:
				# check 2: teamname
				try:
					team_name = user_input
					if len(user_input) > 200:
						await channel.send(f"{emoji_error} The maximum length for an team name is 200 characters. Please try again.")
						continue
				except:
					await channel.send(f"{emoji_error}  Something Wrong with the team name?")
					continue
				first_embed.add_field(name="team_name", value=f"{team_name}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":three: What is the rarity of the item? (Common, Uncommon, Rare, Legendary)"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 3:
				# check 3: rarity
				try:
					rarity = user_input
					if rarity != "common" and rarity != "uncommon" and rarity != "rare" and rarity != "legendary":
						await channel.send(f"{emoji_error}  Invalid rarity given. Please try again or type cancel to exit.")
						continue
				except:
					await channel.send(f"{emoji_error}  Invalid rarity given. Please try again or type cancel to exit.")
					continue
				first_embed.add_field(name="rarity", value=f"{rarity}")
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = ":four: What Position is this player?.\nThis should be no more than 200 characters."
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints += 1

			elif checkpoints == 4:
				# check 4: position
				if len(user_input) > 200:
					await channel.send(f"{emoji_error} The maximum length for an items description is 200 characters. Please try again.")
					continue
				if user_input == "skip":
					position = "generic"
				else:
					position = user_input
				first_embed.add_field(name="position", value=f"{position}", inline=False)
				first_embed.set_footer(text="Type cancel to quit or skip to skip this option")
				next_info = f"{emoji_worked}  Item created successfully!"
				await last_report.edit(content=next_info, embed=first_embed)
				checkpoints = -1
				# finished with the checks
				currently_creating_item = False

		# handler

		try:
			status, create_item_return = await db_handler.create_new_item(item_name, team_name, position, rarity) 
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{create_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

	# ---------------------------
	#   DELETE ITEM
	# ---------------------------

	elif command in ["delete-item", "remove-item"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`delete-item <item name>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		item_name = param[1]

# handler

		try:
			status, remove_item_return = await db_handler.remove_item(item_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106) # green
		embed = discord.Embed(description=f"{emoji_worked}  Item has been removed from the store.\nNote: also deletes from everyone's inventory.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return

	# ---------------------------
	#   BUY BRONZE PACK
	# ---------------------------

	elif command in ["bronze-pack", "bp"]:
		embed = discord.Embed(description=f"A Bronze pack costs 100 coins, and contains 3 cards.\nType `yes` to confirm or anything else to cancel.")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)
		user_input = ""
		# get input first
		user_input = await get_user_input(message)
		print(user_input)
		# check if user wants cancel
		if user_input != "yes":
			await channel.send(f"{emoji_error}  Cancelled command.")
			return

		# handler
		user_role_ids = [randomvar.id for randomvar in message.author.roles]

		try:
			pack_type = "bronze"
			status, buy_pack_return = await db_handler.buy_pack(user, channel, username, user_pfp, pack_type, user_role_ids, server, message.author)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{buy_pack_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return
	
	# ---------------------------
	#   BUY SILVER PACK
	# ---------------------------

	elif command in ["silver-pack", "sp"]:
		embed = discord.Embed(description=f"A Silver pack costs 175 coins, and contains 4 cards.\nType `yes` to confirm or anything else to cancel.")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)
		user_input = ""
		# get input first
		user_input = await get_user_input(message)
		print(user_input)
		# check if user wants cancel
		if user_input != "yes":
			await channel.send(f"{emoji_error}  Cancelled command.")
			return

		# handler
		user_role_ids = [randomvar.id for randomvar in message.author.roles]

		try:
			pack_type = "silver"
			status, buy_pack_return = await db_handler.buy_pack(user, channel, username, user_pfp, pack_type, user_role_ids, server, message.author)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{buy_pack_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return
	
	# ---------------------------
	#   BUY GOLD PACK
	# ---------------------------

	elif command in ["gold-pack", "gp"]:
		embed = discord.Embed(description=f"A Gold pack costs 300 coins, and contains 5 cards with a single guarenteed shiny.\nType `yes` to confirm or anything else to cancel.")
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)
		user_input = ""
		# get input first
		user_input = await get_user_input(message)
		print(user_input)
		# check if user wants cancel
		if user_input != "yes":
			await channel.send(f"{emoji_error}  Cancelled command.")
			return

		# handler
		user_role_ids = [randomvar.id for randomvar in message.author.roles]

		try:
			pack_type = "gold"
			status, buy_pack_return = await db_handler.buy_pack(user, channel, username, user_pfp, pack_type, user_role_ids, server, message.author)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{buy_pack_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return

	# ---------------------------
	#   GIVE ITEM -- can also be used to "sell"
	#				but theyll need to not fuck each other and actually pay up
	# ---------------------------

	elif command in ["give-item"]:
		if "none" in param[1]:  # we need player pinged
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give-item <player pinged> <item name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		player_ping_raw = param[1]
		if len(player_ping_raw) == 22:
			flex_start = 3
		elif len(player_ping_raw) == 21:
			# this should be default...
			flex_start = 2
		elif len(player_ping_raw) == 23:
			flex_start = 4
		player_ping = "".join(list(player_ping_raw[flex_start:-1]))  # gives us only ID

		try:
			user_fetch = client.get_user(int(player_ping))
			print(user_fetch)
			reception_user_name = user_fetch

			if int(player_ping) == user:
				# cannot send money to yourself
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  You cannot trade items with yourself. That would be pointless...", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return

		except:
			# we didnt find him
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<member>` argument given.\n\nUsage:"
											  f"\n`give-item <player pinged> <item> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[2]:  # we need item name
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`give-item <player pinged> <item name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return
		item_name = param[2]

		if "none" in param[3]:  # we need item amount
			amount = 1
		else:
			amount = param[3]

		try:
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`give-item <player pinged> <item name> <amount>`", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `amount` given.\n\nUsage:\n`give-item <player pinged> <item name> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler

		try:
			status, give_item_return = await db_handler.give_item(user, channel, username, user_pfp, item_name, amount, player_ping, server, message.author, reception_user_name)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{give_item_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return

	# ---------------------------
	#   CHECK INVENTORY
	# ---------------------------

	elif command in ["inventory"]:
		
		if "none" in param[1]:	display_mode = "default"
		else: display_mode = param[1]
		try:
			## TODO OHHH MAN it'd be nice to have a better inventory return...
			## TODO: Also would be nice to figure out a way to VIEW all the cards on a similar option
			status, inventory_return = await db_handler.check_inventory(user, channel, username, user_pfp, display_mode)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{inventory_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
			return

	# ---------------------------
	#   ADD ROLE INCOME ROLE
	# ---------------------------

	elif command in ["add-income-role", "add-role-income"]:
		await channel.send("Info: the income amount specified is an hourly one.\nRemember: you need to manually update income.")
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1] or "none" in param[2]:  # we need 3 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`add-income-role <role pinged> <income>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# check role
		income_role_raw = param[1]
		income_role = ""
		if len(income_role_raw) == 22:
			flex_start = 3
		elif len(income_role_raw) == 21:
			flex_start = 2
		elif len(income_role_raw) == 23:
			flex_start = 4
		income_role = "".join(list(income_role_raw[flex_start:-1]))  # gives us only ID
		income_role_try = "".join(list(income_role_raw[flex_start:-2]))  # gives us only ID in the case that role is given as @&
																		 # and not just @ (= 2 chars to remove)

		try:
			role = discord.utils.get(server.roles, id=int(income_role))
		except Exception as e:
			print(f"{e}, but we'll try again.")

		try:
			role = discord.utils.get(server.roles, id=int(income_role_try))
		except Exception as e:
			print(e)
			await channel.send(f"{emoji_error}  Invalid role given, (second check not passed either). Please try again.")
			return
		
		# check amount
		amount = param[2]
		# they can use the thousands separator comma
		try:
			newAmount = []
			for char in amount:
				if char != ",":
					newAmount.append(char)
			amount = "".join(newAmount)
			amount = int(amount)
			if amount < 1:
				color = discord_error_rgb_code
				embed = discord.Embed(
					description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-income-role <role pinged> <amount>`",
					color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Invalid `<amount>` argument given.\n\nUsage:\n`add-income-role <role pinged> <amount>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# handler
		try:
			status, create_role_return = await db_handler.new_income_role(user, channel, username, user_pfp, income_role, amount)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{create_role_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   REMOVE ROLE
	# ---------------------------

	elif command in ["remove-income-role", "delete-income-role", "remove-role-income", "delete-role-income"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		if "none" in param[1]:  # we need 1 parameters
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"{emoji_error}  Too few arguments given.\n\nUsage:\n`remove-income-role <role pinged>`", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		# check role

		income_role_raw = param[1]
		income_role = ""
		if len(income_role_raw) == 22:
			flex_start = 3
		elif len(income_role_raw) == 21:
			flex_start = 2
		elif len(income_role_raw) == 23:
			flex_start = 4
		income_role = "".join(list(income_role_raw[flex_start:-1]))  # gives us only ID

		try:
			role = discord.utils.get(server.roles, id=int(income_role))
		except Exception as e:
			print(e)
			await channel.send(f"{emoji_error}  Invalid role given. Please try again.")
			return

		# handler
		try:
			status, remove_role_return = await db_handler.remove_income_role(user, channel, username, user_pfp, income_role)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{remove_role_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106)  # green
		embed = discord.Embed(description=f"{emoji_worked}  Role has been disabled as income role.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return

	# ---------------------------
	#   LIST INCOME ROLES
	# ---------------------------

	elif command in ["list-roles", "list-income-roles", "list-role-income", "list-incomes"]:
		try:
			status, list_roles_return = await db_handler.list_income_roles(user, channel, username, user_pfp, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{list_roles_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)
		return

	# ---------------------------
	#   UPDATE INCOMES
	# ---------------------------

	elif command in ["update-income"]:
		if not staff_request:
			color = discord_error_rgb_code
			embed = discord.Embed(description=f"🔒 Requires botmaster role", color=color)
			embed.set_author(name=username, icon_url=user_pfp)
			await channel.send(embed=embed)
			return

		try:
			status, update_incomes_return = await db_handler.update_incomes(user, channel, username, user_pfp, server)
			if status == "error":
				color = discord_error_rgb_code
				embed = discord.Embed(description=f"{update_incomes_return}", color=color)
				embed.set_author(name=username, icon_url=user_pfp)
				await channel.send(embed=embed)
				return
		except Exception as e:
			print(e)
			await send_error(channel)

		color = discord.Color.from_rgb(102, 187, 106)  # green
		embed = discord.Embed(description=f"{emoji_worked}  Users with registered roles have received their income.", color=color)
		embed.set_author(name=username, icon_url=user_pfp)
		await channel.send(embed=embed)

		return
	if(message.content.startswith("/")):
		await message.delete()

		return


"""
END OF CODE.
	-> starting bot
"""

print("Starting bot")
client.run(token)
