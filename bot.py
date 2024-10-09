import discord
import os
import requests
import asyncio
import re  # For regular expression operations
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1293682301821259898  # Replace with your Discord channel ID
URL_TO_CHECK = 'https://agscomics.com/wp-json/wp/v2/posts'  # WordPress REST API URL

# Create intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def post_update(post):
    channel = client.get_channel(CHANNEL_ID)

    # Build the title for the embed
    title = post['title']['rendered']
    url = post['link']
    
    # Create an embed message with the title only
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

    # Send the embed to the channel
    await channel.send(embed=embed)

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
                print("No posts found.")
        else:
            print(f"Failed to fetch posts: {response.status_code}")
        
        await asyncio.sleep(60)  # Check for updates every minute

client.run(TOKEN)
