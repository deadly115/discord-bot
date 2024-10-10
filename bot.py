import discord
import os
import requests
import asyncio
import re
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_1 = 1293682301821259898  # First channel ID
CHANNEL_ID_2 = 854986887370244116   # Second channel ID
URL_TO_CHECK = 'https://agscomics.com/wp-json/wp/v2/posts'  # WordPress REST API URL
ALL_SERIES_ROLE_ID = 878685403266306130  # 'All series' role ID

# Create intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
client = discord.Client(intents=intents)

# Function to clean and format title for role matching
def clean_title_for_role(title):
    # Remove everything after the last hyphen and replace special characters with spaces
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', '', title.split('–')[-1]).strip()
    formatted_title = re.sub(r'\s+', ' ', formatted_title)  # Replace multiple spaces with a single space
    return formatted_title

# Function to find the closest matching role
def find_closest_role(guild, formatted_title):
    max_match = 0
    closest_role = None
    title_words = set(formatted_title.lower().split())

    for role in guild.roles:
        role_words = set(role.name.lower().split())
        match_count = len(title_words & role_words)  # Count matching words
        if match_count > max_match:
            max_match = match_count
            closest_role = role

    return closest_role

async def post_update(post):
    title = post['title']['rendered']
    url = post['link']

    # Create the embed message
    embed = discord.Embed(title=title, url=url)

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
        match = re.search(r'<img[^>]+src="([^">]+)"', content_rendered)
        if match:
            media_url = match.group(1)
        else:
            print(f"No image found in content for post ID {post['id']}")

    if media_url:
        embed.set_image(url=media_url)

    # Get both channels
    channel_1 = client.get_channel(CHANNEL_ID_1)
    channel_2 = client.get_channel(CHANNEL_ID_2)

    # Get the current guild from the channel
    guild = channel_1.guild

    # Find the closest role based on title
    formatted_title = clean_title_for_role(title)
    closest_role = find_closest_role(guild, formatted_title)

    # Ensure we have a matching role to mention, otherwise skip mentioning
    if closest_role:
        ping_message = f":mega: <@&{ALL_SERIES_ROLE_ID}> <@&{closest_role.id}>"
    else:
        ping_message = f":mega: <@&{ALL_SERIES_ROLE_ID}>"

    # Send the ping and the embed to both channels
    await channel_1.send(ping_message)
    await channel_1.send(embed=embed)

    await channel_2.send(ping_message)
    await channel_2.send(embed=embed)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await check_for_updates()

async def check_for_updates():
    last_post_id = None  # Variable to keep track of the last posted ID
    while True:
        response = requests.get(URL_TO_CHECK)
        if response.status_code == 200:
            posts = response.json()
            if posts:
                latest_post = max(posts, key=lambda post: post['id'])
                if last_post_id is None or latest_post['id'] > last_post_id:
                    await post_update(latest_post)  # Send update for the latest post
                    last_post_id = latest_post['id']  # Update the last posted ID
                    print(f"Posted ID: {last_post_id}")
            else:
                print("No posts found.")
        else:
            print(f"Failed to fetch posts: {response.status_code}")

        await asyncio.sleep(60)  # Check for updates every minute

client.run(TOKEN)
