async def post_update(post, guild):
    title = post['title']['rendered']
    url = post['link']
    
    # Remove special characters and everything after the last hyphen for the role mention
    formatted_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title.rsplit('–', 1)[0]).strip()
    formatted_title = re.sub(r'\s+', ' ', formatted_title)  # Replace multiple spaces with a single space

    # Find the role by the best match
    role = find_best_role_match(guild, formatted_title)
    
    # Create the embed message
    embed = discord.Embed(
        title=title,
        url=url,
        description="Check out the latest update!",
        color=discord.Color.blurple()  # You can choose any color here
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

    # Add author and footer information
    embed.set_author(name="AGS Updates", icon_url="https://example.com/icon.png")  # Replace with your icon URL
    embed.set_footer(text="Stay updated with AGS Comics!", icon_url="https://example.com/footer-icon.png")  # Replace with your footer icon URL

    # Send the ping and the embed to all channels
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        if channel:
            if role:
                await channel.send(f":mega: <@&{ALL_SERIES_ROLE_ID}> <@&{role.id}>")  # Mention the dynamic role and @All series
            else:
                await channel.send(f":mega: <@&{ALL_SERIES_ROLE_ID}>")  # If no role is found, just @All series
            
            await channel.send(embed=embed)
        else:
            print(f"Channel {channel_id} not found or not accessible.")
