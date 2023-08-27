import discord
import requests
import random
from discord.ext import commands
from youtube_dl import YoutubeDL

TOKEN = #######
intents = discord.Intents.all()  # Intents to work with members, messages, etc.
YOUTUBE_API_KEY = 'AIzaSyCjTmqTxRFfaoadqJySQ0C3HKizVndZrIU'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="The Beatles"))


@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel!")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)

@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

# Get the YouTube URL based on song name
def get_youtube_url(query):
    params = {
        'part': 'snippet',
        'q': query,
        'key': YOUTUBE_API_KEY,
        'maxResults': 1,
        'type': 'video'
    }
    
    response = requests.get(YOUTUBE_SEARCH_URL, params=params).json()
    items = response.get('items')
    
    if not items:
        return None
    
    video_id = items[0]['id']['videoId']
    return f'https://www.youtube.com/watch?v={video_id}'
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


@bot.command()
async def play(ctx, *, song_name):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return

    channel = ctx.message.author.voice.channel
    
    # Check if the bot is already connected in the guild
    if ctx.voice_client is None:
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
    
    song_url = get_youtube_url(song_name)
    if not song_url:
        await ctx.send("Song not found.")
        return

    ydl_opts = {'format': 'bestaudio'}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song_url, download=False)
        url2 = info['formats'][0]['url']
        song_title = info['title'] 
        await ctx.send(f"Now playing: {song_title}")
        if not voice_client.is_playing():
            voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=url2, **FFMPEG_OPTIONS))
        else:
            await ctx.send("Already playing a song!")

@bot.command()
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Stopped the song!")
    else:
        await ctx.send("No song is currently playing.")
        

current_trivia = {}  # Store ongoing trivia for users

BEATLES_TRIVIA_QUESTIONS = [
    {
        "question": "Which Beatles album was released in 1967 and is often considered one of the greatest albums in the history of music?",
        "answer": "sgt. pepper's lonely hearts club band",
        "options": ["The White Album", "Abbey Road", "Sgt. Pepper's Lonely Hearts Club Band", "Let It Be"]
    },
    {
        "question": "Who was the drummer for The Beatles?",
        "answer": "ringo starr",
        "options": ["John Lennon", "Paul McCartney", "George Harrison", "Ringo Starr"]
    },
]

@bot.command()
async def beatles_trivia(ctx):
    # Check if user is already playing
    if ctx.author.id in current_trivia:
        await ctx.send("You're already playing! Answer the current question or type `!endtrivia` to stop.")
        return

    # Select a random trivia question
    question = random.choice(BEATLES_TRIVIA_QUESTIONS)
    current_trivia[ctx.author.id] = question

    # Send the trivia question with its options
    options = "\n".join([f"{idx + 1}. {opt}" for idx, opt in enumerate(question['options'])])
    await ctx.send(f"{question['question']}\n\n{options}")

@bot.command()
async def answer(ctx, choice: int):
    # Check if user is playing
    if ctx.author.id not in current_trivia:
        await ctx.send("You're not playing trivia. Start with `!beatles_trivia`.")
        return

    question = current_trivia[ctx.author.id]
    if question["answer"] == question["options"][choice - 1].lower():
        await ctx.send("Correct!")
    else:
        await ctx.send(f"Wrong! The correct answer is: {question['answer']}.")

    # End the trivia for this user
    del current_trivia[ctx.author.id]

@bot.command()
async def endtrivia(ctx):
    # Check if user is playing
    if ctx.author.id not in current_trivia:
        await ctx.send("You're not playing trivia. Start with `!beatles_trivia`.")
        return

    # End the trivia for this user
    del current_trivia[ctx.author.id]
    await ctx.send("Trivia ended.")

bot.run(TOKEN)
