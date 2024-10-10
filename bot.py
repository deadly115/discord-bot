import discord
import os
import requests
import asyncio
import re  # For regular expression operations
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_1 = 1293682301821259898  # First Discord channel ID
CHANNEL_ID_2 = 854986887370244116   # Second Discord channel ID
URL_TO_CHECK = 'https://agscomics.com/wp-json/wp/v2/posts'  # WordPress REST API URL

# Create intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def post_update(post):
    # Get both channels by their IDs
    channel_1 = client.get_channel(CHANNEL_ID_1)
    channel_2 = client.get_channel(CHANNEL_ID_2)

    # Get the title and URL for the embed
    title = post['title']['rendered']
    url = post['link']
    
    # Format the title for the role mention (but keep the original title for the embed)
    if '–' in title:
        formatted_title = title.rsplit('–', 1)[0].strip()  # Remove everything after the last '–'
    elif '-' in title:
        formatted_title = title.rsplit('-', 1)[0].strip()  # Remove everything after the last '-'
    else:
        formatted_title = title.strip()

    # Replace special characters in the formatted title for the role mention
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', formatted_title)
    formatted_title = re.sub(r'\s+', ' ', formatted_title).strip()  # Replace multiple spaces with a single space

    # Create an embed message with the original title
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
        # Use a regex to find the first image in the content
        match = re.search(r'<img[^>]+src="([^">]+)"', content_rendered)
        if match:
            media_url = match.group(1)
        else:
            print(f"No image found in content for post ID {post['id']}")

    # Set the image URL in the embed if available
    if media_url:
        embed.set_image(url=media_url)

    # Send the ping and the embed to both channels
    message = f":mega: @All series @{formatted_title}"  # Pinging roles
    await channel_1.send(message)
    await channel_1.send(embed=embed)

    await channel_2.send(message)
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
                # Sort posts by ID to ensure we get the latest
                latest_post = max(posts, key=lambda post: post['id'])
                if last_post_id is None or latest_post['id'] > last_post_id:
                    await post_update(latest_post)  # Send update for the latest post
                    last_post_id = latest_post['id']  # Update the last posted ID
                    print(f"Posted ID: {last_post_id}")  # Log the posted ID for debugging
            else:
        



