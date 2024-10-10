import discord
import os
import requests
import asyncio
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_1 = 1293682301821259898  # First channel ID
CHANNEL_ID_2 = 854986887370244116   # Second channel ID
URL_TO_CHECK = 'https://agscomics.com/wp-json/wp/v2/posts'  # WordPress REST API URL
ALL_SERIES_ROLE_ID = 878685403266306130  # 'All series' role ID

# Create intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def post_update(post):
    title = post['title']['rendered']
    url = post['link']

    # Extract and format the title for role mention
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', '', title.split('–')[-1]).strip()
    formatted_title = re.sub(r'\s+', ' ', formatted_title)  # Replace multiple spaces with a single space
    
    # Get channel references
    channel_1 = client.get_channel(CHANNEL_ID_1)
    channel_2 = client.get_channel(CHANNEL_ID_2)
    
    # Ensure the channels exist
    if channel_1 is None or channel_2 is None:
        print("Error: One or both channels not found.")
        return

    # Build the embed
    embed = discord.Embed(title=title, url=url)
    
    # Check for featured media (cover image)
    media_url = None
    if 'featured_media' in post and post['featured_media'] > 0:
        media_response = requests.get(f'https://agscomics.com/wp-json/wp/v2/media/{post["featured_media"]}')
        if media_response.status_code == 200:
            media = media_response.json()
            media_url = media['source_url']
    else:
        # Extract the first image from the content if no featured media
        content_rendered = post['content']['rendered']
        match = re.search(r'<img[^>]+src="([^">]+)"', content_rendered)
        if match:
            media_url = match.group(1)
        else:
            print(f"No image found in content for post ID {post['id']}")

    # Set image URL in embed if available
    if media_url:
        embed.set_image(url=media_url)

    # Attempt to send the message to both channels
    try:
        await channel_1.send(f"<@&{ALL_SERIES_ROLE_ID}> @{formatted_title}", embed=embed)
        print(f"Message sent to Channel 1 (ID: {CHANNEL_ID_1})")
    except Exception as e:
        print(f"Error sending message to Channel 1: {e}")
    
    try:
        await channel_2.send(f"<@&{ALL_SERIES_ROLE_ID}> @{formatted_title}", embed=embed)
        print(f"Message sent to Channel 2 (ID: {CHANNEL_ID_2})")
    except Exception as e:
        print(f"Error sending message to Channel 2: {e}")

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
                    print(f"Posted ID: {last_post_id}")  # Log the posted ID for debugging
            else:
                print("No posts found.")
        else:
            print(f"Failed to fetch posts: {response.status_code}")
        
        await asyncio.sleep(60)  # Check for updates every minute

# Run the bot
client.run(TOKEN)
