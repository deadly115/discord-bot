import discord
import os
import requests
import asyncio
import re  # For regular expression operations
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_IDS = [1293682301821259898, 854986887370244116]  # List of channels to send updates to
URL_TO_CHECK = 'https://agscomics.com/wp-json/wp/v2/posts'  # WordPress REST API URL

# Create intents
intents = discord.Intents.default()
intents.guilds = True  # To access guild (server) info and roles
client = discord.Client(intents=intents)

ALL_SERIES_ROLE_ID = 878685403266306130  # 'All series' role ID

# Helper function to find the best matching role by name based on word similarity
def find_best_role_match(guild, formatted_title):
    formatted_words = set(formatted_title.lower().split())

    best_match = None
    highest_match_count = 0

    for role in guild.roles:
        role_words = set(role.name.lower().split())
        common_words = formatted_words.intersection(role_words)
        match_count = len(common_words)

        if match_count > highest_match_count:
            highest_match_count = match_count
            best_match = role

    return best_match

async def post_update(post, guild):
    print(f"Received post update: {post}")  # Debugging line
    title = post['title']['rendered']
    url = post['link']
    
    # Remove special characters and everything after the last hyphen for the role mention
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title.rsplit('–', 1)[0]).strip()
    formatted_title = re.sub(r'\s+', ' ', formatted_title)  # Replace multiple spaces with a single space

    # Find the role by the best match
    role = find_best_role_match(guild, formatted_title)

    # Create the embed message with a glittery border effect
    embed = discord.Embed(
        title=title,
        url=url,
        description="Check out the latest update!",
        color=0xFFD700  # Gold color to simulate glitter
    )
    
    # Check for featured media (cover image)
    media_url = None
    if 'featured_media' in post and post['featured_media'] > 0:
        media_response = requests.get(f'https://agscomics.com/wp-json/wp/v2/media/{post["featured_media"]}')
        if media_response.status_code == 200:
            media = media_response.json()
            media_url = media['source_url']
    else:
        # If no featured image, extract the image from the content
        content_rendered = post['content']['rendered']
        # Use a regex to find the first image in the content
        match = re.search(r'<img[^>]+src="([^">]+)"', content_rendered)
        if match:
            media_url = match.group(1)
        else:
            print(f"No image found in content for post ID {post['id']}")

    # Set the image URL in the embed if available
    if media_url:
        embed.set_image(url=media_url)

    print(f"Sending update to channels: {CHANNEL_IDS}")  # Debugging line

    # Send the ping and the embed to all channels
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        if channel:
            if role:
                await channel.send(f":mega: <@&{ALL_SERIES_ROLE_ID}> <@&{role.id}>")  # Mention the dynamic role and @All series
            else:
                await channel.send(f":mega: <@&{ALL_SERIES_ROLE_ID}>")  # If no role is found, just @All series
            
            await channel.send(embed=embed)
            print(f"Message sent to channel: {channel_id}")  # Debugging line
        else:
            print(f"Channel {channel_id} not found or not accessible.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    guild = discord.utils.get(client.guilds)  # Assuming the bot is in one guild
    await check_for_updates(guild)

async def check_for_updates(guild):
    last_post_id = None  # Variable to keep track of the last posted ID
    while True:
        response = requests.get(URL_TO_CHECK)
        print(f"Checking for updates: {response.status_code}")  # Debugging line
        if response.status_code == 200:
            posts = response.json()
            print(f"Posts retrieved: {posts}")  # Debugging line
            if posts:
                # Sort posts by ID to ensure we get the latest
                latest_post = max(posts, key=lambda post: post['id'])
                if last_post_id is None or latest_post['id'] > last_post_id:
                    await post_update(latest_post, guild)  # Send update for the latest post
                    last_post_id = latest_post['id']  # Update the last posted ID
                    print(f"Posted ID: {last_post_id}")  # Log the posted ID for debugging
            else:
                print("No posts found.")
        else:
            print(f"Failed to fetch posts: {response.status_code}")
        
        await asyncio.sleep(60)  # Check for updates every minute

client.run(TOKEN)
