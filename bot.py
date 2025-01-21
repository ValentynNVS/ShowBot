import discord
from discord.ext import commands
import json
from datetime import datetime

# Define the intents you want your bot to use
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Create the bot instance with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents)
# Load data from the JSON file
def load_data():
    try:
        with open('mmr_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data to the JSON file
def save_data(data):
    with open('mmr_data.json', 'w') as f:
        json.dump(data, f, indent=4)

# Load data at the start of the bot
data = load_data()

# Structure to store match history
match_history = []

# Load match history from file
def load_match_history():
    try:
        with open('match_history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save match history to file
def save_match_history():
    with open('match_history.json', 'w') as f:
        json.dump(match_history, f, indent=4)

match_history = load_match_history()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot is connected to Discord as {bot.user}')

@bot.command()
async def register(ctx, steam_link: str):
    user_id = str(ctx.author.id)  # Ensure user ID is stored as a string
    if user_id in data:
        await ctx.send(f'{ctx.author.name}, you are already registered. Use `!userinfo` to see your profile.')
    else:
        data[user_id] = {
            'username': ctx.author.name,
            'mmr': 200,
            'wins': 0,
            'losses': 0,
            'steam_link': steam_link
        }
        save_data(data)
        await ctx.send(f'{ctx.author.name} has been registered with 200 MMR and Steam link: {steam_link}')


# Command to record a win
@bot.command()
async def win(ctx):
    user_id = str(ctx.author.id)
    if user_id not in data:
        await ctx.send(f'{ctx.author.name}, you are not registered. Please register first using `!register <your_steam_link>`.')
    else:
        data[user_id]['mmr'] += 30
        data[user_id]['wins'] += 1
        save_data(data)
        await ctx.send(f'{ctx.author.name} won a match! Their new MMR is {data[user_id]["mmr"]}.')

# Command to record a loss
@bot.command()
async def lose(ctx):
    user_id = str(ctx.author.id)
    if user_id not in data:
        await ctx.send(f'{ctx.author.name}, you are not registered. Please register first using `!register <your_steam_link>`.')
    else:
        data[user_id]['mmr'] -= 30
        data[user_id]['losses'] += 1
        save_data(data)
        await ctx.send(f'{ctx.author.name} lost a match. Their new MMR is {data[user_id]["mmr"]}.')

# Command to show user info
@bot.command()
async def userinfo(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    user_id = str(user.id)
    if user_id not in data:
        await ctx.send(f'{user.name} is not registered. Use `!register <your_steam_link>` to register.')
    else:
        profile = data[user_id]
        await ctx.send(f"**{profile['username']}**'s Profile:\n"
                       f"MMR: {profile['mmr']}\n"
                       f"Wins: {profile['wins']}\n"
                       f"Losses: {profile['losses']}\n"
                       f"Steam Profile: {profile['steam_link']}")

# Record a match between two teams
@bot.command()
async def record_match(ctx, channel_a: discord.VoiceChannel, channel_b: discord.VoiceChannel):
    team_a = [member.name for member in channel_a.members]
    team_b = [member.name for member in channel_b.members]

    if not team_a or not team_b:
        await ctx.send("Both teams need to have players in the voice channels.")
        return

    match_id = len(match_history) + 1  # Create a unique match ID
    match = {
        "id": match_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "team_A": team_a,
        "team_B": team_b,
        "winner": "Pending",  # Set winner to Pending initially
        "dota_id": None  # Initialize Dota ID as None
    }
    
    match_history.append(match)
    save_match_history()

    await ctx.send(f"Match recorded! ID: {match_id}, Team A: {team_a}, Team B: {team_b}, Winner: Pending")

@bot.command()
async def update_winner(ctx, match_id: int, new_winner: int):
    global match_history
    for match in match_history:
        if match['id'] == match_id:
            if new_winner not in [1, 2]:
                await ctx.send("Please specify '1' for Team A or '2' for Team B as the winner.")
                return
            
            if match['winner'] != "Pending" : 
                checkMatchWinner = int(match['winner'])
                if new_winner == checkMatchWinner: 
                    await ctx.send("The team is already marked as winners")
                    return
            


 
            
            # Determine winning and losing teams
            winning_team = match['team_A'] if new_winner == 1 else match['team_B']
            losing_team = match['team_B'] if new_winner == 1 else match['team_A']

            # Initialize lists to hold player updates
            player_updates = []

            # Update MMR and wins for the winning team
            for player_name in winning_team:
                user_id = None
                # Standard for loop to find user_id
                for uid, profile in data.items():
                    if profile['username'] == player_name:
                        user_id = uid
                        break  # Exit the loop once found

                if user_id is not None:  # Make sure user_id is valid
                    data[user_id]['mmr'] += 30
                    data[user_id]['wins'] += 1
                    player_updates.append((data[user_id]['username'], 'win', data[user_id]['mmr']))

            # Update MMR and losses for the losing team
            for player_name in losing_team:
                user_id = None
                # Standard for loop to find user_id
                for uid, profile in data.items():
                    if profile['username'] == player_name:
                        user_id = uid
                        break  # Exit the loop once found

                if user_id is not None:
                    data[user_id]['mmr'] -= 30
                    data[user_id]['losses'] += 1
                    player_updates.append((data[user_id]['username'], 'loss', data[user_id]['mmr']))

            # Update the match winner in the match history
            match['winner'] = f"{new_winner}"  # Store the winner as "Team 1" or "Team 2"
            save_data(data)  # Save updated user data
            save_match_history()  # Save updated match history

            # Create a message summarizing the updates
            update_messages = []
            for username, result, mmr in player_updates:
                if result == 'win':
                    update_messages.append(f"{username} won! New MMR: {mmr}.")
                else:
                    update_messages.append(f"{username} lost. New MMR: {mmr}.")

            await ctx.send(f"Updated match ID {match_id}: New winner is Team {new_winner}.\n" + "\n".join(update_messages))
            return
            
    await ctx.send(f"No match found with ID {match_id}.")



@bot.command()
async def Igor(ctx):
    await ctx.send("Pidor")


# Command to add Dota ID to a match
@bot.command()
async def add_dota_id(ctx, match_id: int, dota_id: str):
    global match_history
    for match in match_history:
        if match['id'] == match_id:
            match['dota_id'] = dota_id
            save_match_history()
            await ctx.send(f"Added Dota ID {dota_id} to match ID {match_id}.")
            return
    await ctx.send(f"No match found with ID {match_id}.")

# Command to display recent matches
@bot.command()
async def recent_matches(ctx, count: int = 5):
    if not match_history:
        await ctx.send("No matches have been recorded yet.")
        return
    
    recent = match_history[-count:]  # Get the last 'count' matches
    recent.reverse()  # Reverse to show the most recent first

    for match in recent:
        match_details = (
            f"**Match ID**: {match['id']}\n"
            f"**Date**: {match['date']}\n"
            f"**Time**: {match['time']}\n"
            f"**Team A**: {', '.join(match['team_A'])}\n"
            f"**Team B**: {', '.join(match['team_B'])}\n"
            f"**Winner**: {match['winner']}\n"
            f"**Dota ID**: {match['dota_id'] if match['dota_id'] else 'Not set'}\n"
        )
        await ctx.send(match_details)
        await ctx.send("------------------------------------------------------------")

# Delete profile command
@bot.command()
async def delete(ctx):
    user_id = str(ctx.author.id)
    if user_id not in data:
        await ctx.send(f'{ctx.author.name}, you are not registered. No profile to delete.')
    else:
        del data[user_id]
        save_data(data)
        await ctx.send(f'{ctx.author.name}, your profile has been deleted successfully.')


@bot.command()
async def leaderboard(ctx):
    if not data:
        await ctx.send("No profiles are currently registered.")
        return

    # Initialize a list to hold tuples of (username, mmr)
    player_mmr_list = []

    # Iterate through the data to populate the list
    for user_id, profile in data.items():
        if 'mmr' in profile:  # Check if 'mmr' exists in the profile
            player_mmr_list.append((profile['username'], profile['mmr']))

    # Sort the list by MMR in descending order
    sorted_players = sorted(player_mmr_list, key=lambda x: x[1], reverse=True)

    leaderboard_text = "**Leaderboard:**\n"

    for index, (username, mmr) in enumerate(sorted_players, start=1):
        leaderboard_text += f"{index}. **{username}** - MMR: {mmr}\n"

    await ctx.send(leaderboard_text)




# Commands help message
@bot.command(name='commands')
async def commands_list(ctx):
    help_text = (
        "**Showmatch Tracker Commands:**\n"
        "`!register <your_steam_link>` - Register your Steam profile.\n"
        "Example: `!register https://steamcommunity.com/id/yourprofile`\n\n"
        "`!win` - Record a win in your showmatch.\n"
        "`!lose` - Record a loss in your showmatch.\n"
        "`!give_win @user` - Award a win to a specific user.\n"
        "`!give_loss @user` - Record a loss for a specific user.\n"
        "`!userinfo [user]` - Show your user profile and stats or another user's profile.\n"
        "`!record_match <voice_channel_A> <voice_channel_B>` - Record a match between two teams.\n"
        "`!update_winner <match_id> <new_winner>` - Update the winner for a recorded match.\n"
        "`!add_dota_id <match_id> <dota_id>` - Add Dota ID to a recorded match.\n"
        "`!recent_matches [count]` - Show the last few recorded matches.\n"
        "`!delete` - Delete your profile from the tracker.\n"
        "`!leaderboard` - Display the top players based on MMR.\n"
    )
    await ctx.send(help_text)

@bot.command()
async def give_win(ctx, user: discord.Member):
    user_id = str(user.id)
    if user_id not in data:
        await ctx.send(f'{user.name} is not registered. They need to register first using `!register <your_steam_link>`.')
    else:
        data[user_id]['mmr'] += 30
        data[user_id]['wins'] += 1
        save_data(data)
        await ctx.send(f'{user.name} has been awarded a win! Their new MMR is {data[user_id]["mmr"]}.')

@bot.command()
async def give_loss(ctx, user: discord.Member):
    user_id = str(user.id)
    if user_id not in data:
        await ctx.send(f'{user.name} is not registered. They need to register first using `!register <your_steam_link>`.')
    else:
        data[user_id]['mmr'] -= 30
        data[user_id]['losses'] += 1
        save_data(data)
        await ctx.send(f'{user.name} has been given a loss. Their new MMR is {data[user_id]["mmr"]}.')

bot.run("Oops, cant let you know my API key")

