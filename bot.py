import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import json
import random
import re
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Config - Works on both Windows and Linux (Render.com)
import platform
if platform.system() == 'Linux':
    # Render.com uses Linux
    FFMPEG_PATH = 'ffmpeg'  # Use system FFmpeg
else:
    # Local Windows
    BOT_FOLDER = r'C:\Users\gmelc\Desktop\spotify-bot'
    FFMPEG_PATH = os.path.join(BOT_FOLDER, 'ffmpeg-master-latest-win64-gpl-shared', 'bin', 'ffmpeg.exe')

PLAYLIST_FILE = os.path.join(BOT_FOLDER, 'playlists.json')
VOLUME_FILE = os.path.join(BOT_FOLDER, 'volumes.json')
SETTINGS_FILE = os.path.join(BOT_FOLDER, 'settings.json')
STATS_FILE = os.path.join(BOT_FOLDER, 'stats.json')
RADIO_FILE = os.path.join(BOT_FOLDER, 'radio_cache.json')

# Data storage
playlists = {}
volumes = {}
queues = {}
current_players = {}
search_sessions = {}
settings = {}
stats = {}
user_favorites = {}
loop_modes = {}
radio_sessions = {}
user_stats = {}
guild_stats = {}
radio_cache = {}  # Store similar songs for any track
song_relationships = {}  # Track which songs are similar
user_moods = {}  # Track user mood preferences
party_modes = {}  # Party mode settings
karaoke_sessions = {}  # Karaoke mode
duel_sessions = {}  # Music battles
song_history = {}  # ADD THIS LINE

# Expanded genres with sub-genres
GENRES = {
    'pop': ['pop hits 2024', 'top pop songs', 'popular music', 'mainstream hits', 'radio hits'],
    'hiphop': ['hip hop 2024', 'rap hits', 'trap music', 'drill music', 'underground rap', 'old school hip hop'],
    'rock': ['rock hits 2024', 'alternative rock', 'classic rock', 'indie rock', 'punk rock', 'metalcore'],
    'electronic': ['edm 2024', 'electronic dance music', 'house music', 'techno', 'dubstep', 'trance', 'synthwave'],
    'rnb': ['r&b 2024', 'soul music', 'rnb hits', 'neo soul', 'contemporary r&b'],
    'country': ['country hits 2024', 'top country songs', 'country pop', 'classic country'],
    'jazz': ['jazz music', 'smooth jazz', 'jazz hits', 'bebop', 'fusion jazz'],
    'classical': ['classical music', 'orchestra', 'piano music', 'violin concerto', 'symphony'],
    'lofi': ['lofi hip hop', 'chill beats', 'study music', 'jazz hop', 'chillhop'],
    'metal': ['metal music', 'heavy metal', 'rock metal', 'death metal', 'progressive metal'],
    'reggae': ['reggae hits', 'bob marley', 'reggae music', 'dub', 'dancehall'],
    'latin': ['latin hits 2024', 'reggaeton', 'latin pop', 'bachata', 'salsa', 'dembow'],
    'kpop': ['kpop 2024', 'bts', 'blackpink', 'korean pop', 'newjeans', 'ive', 'stray kids'],
    'anime': ['anime openings', 'japanese music', 'anime songs', 'jpop', 'vocaloid'],
    'gaming': ['gaming music', 'epic gaming mix', 'valorant music', 'csgo music', 'fortnite songs'],
    'workout': ['workout music', 'gym motivation', 'workout mix', 'running music', 'pump up songs'],
    'study': ['study music', 'focus music', 'concentration music', 'reading music'],
    'sleep': ['sleep music', 'relaxing music', 'rain sounds', 'asmr music', 'meditation'],
    'party': ['party music', 'club hits', 'dance music', 'festival music', 'friday night'],
    'throwback': ['2000s hits', '90s music', 'old school hits', '80s hits', 'classic hits'],
    'indie': ['indie music', 'indie pop', 'indie folk', 'bedroom pop', 'alternative indie'],
    'blues': ['blues music', 'delta blues', 'electric blues', 'soul blues'],
    'funk': ['funk music', 'funky hits', 'groovy music', 'pfunk'],
    'disco': ['disco hits', 'funky disco', 'nu disco', 'disco fever'],
    'punk': ['punk rock', 'pop punk', 'hardcore punk', 'skate punk'],
    'soul': ['soul music', 'motown', 'northern soul', 'deep soul'],
    'gospel': ['gospel music', 'christian music', 'praise and worship', 'choir'],
    'folk': ['folk music', 'folk rock', 'americana', 'bluegrass'],
    'world': ['afrobeats', 'bollywood', 'samba', 'cumbia', 'celtic music']
}

# Moods with intensity levels
MOODS = {
    'happy': ['happy music', 'feel good songs', 'upbeat music', 'joyful songs', 'sunny day'],
    'sad': ['sad songs', 'melancholy music', 'emotional songs', 'heartbreak songs', 'crying music'],
    'angry': ['angry music', 'rage mix', 'intense music', 'break stuff', 'mad songs'],
    'chill': ['chill music', 'relaxing vibes', 'calm songs', 'chillout', 'laid back'],
    'hype': ['hype music', 'energy boost', 'pump up songs', 'adrenaline music', 'intense workout'],
    'romantic': ['love songs', 'romantic music', 'date night', 'sexy songs', 'slow jams'],
    'focus': ['focus music', 'deep work', 'productivity music', 'flow state', 'concentration'],
    'party': ['party mix', 'dance party', 'celebration music', 'turn up', 'lit songs'],
    'nostalgic': ['nostalgic songs', 'throwback feels', 'memories music', 'childhood songs'],
    'mysterious': ['dark music', 'mysterious vibes', 'noir jazz', 'creepy ambient'],
    'epic': ['epic music', 'cinematic', 'trailer music', 'heroic orchestral'],
    'cozy': ['cozy music', 'warm vibes', 'coffee shop', 'autumn playlist']
}

# Time-based playlists
TIME_PLAYLISTS = {
    'morning': ['morning coffee', 'wake up music', 'sunrise vibes', 'early bird'],
    'afternoon': ['afternoon chill', 'sunny day', 'lunch break music'],
    'evening': ['sunset music', 'golden hour', 'wind down'],
    'night': ['night drive', 'midnight vibes', 'late night', 'after dark'],
    'weekend': ['weekend vibes', 'saturday night', 'sunday chill', 'friday feeling']
}

# Weather-based (user can set)
WEATHER_MOODS = {
    'sunny': ['sunny day music', 'summer hits', 'bright and happy'],
    'rainy': ['rainy day jazz', 'cozy rain', 'melancholy rain'],
    'snowy': ['winter music', 'cozy fireplace', 'christmas vibes'],
    'stormy': ['storm music', 'dark and moody', 'intense weather'],
    'cloudy': ['cloudy day', 'grey skies', 'mellow vibes']
}

# Special modes
SPECIAL_MODES = {
    'focus': {'name': '🎯 Focus Mode', 'desc': 'No distractions, optimal study beats', 'filter': 'flat'},
    'party': {'name': '🎉 Party Mode', 'desc': 'Auto-DJ, seamless transitions', 'filter': 'bassboost'},
    'chill': {'name': '🌊 Chill Mode', 'desc': 'Smooth transitions, no sudden changes', 'filter': 'slowed'},
    'workout': {'name': '💪 Beast Mode', 'desc': 'High energy, no slow songs', 'filter': 'loud'},
    'sleep': {'name': '🌙 Sleep Mode', 'desc': 'Gradually decreasing volume', 'filter': 'slowed'},
    'karaoke': {'name': '🎤 Karaoke Mode', 'desc': 'Instrumental versions when available', 'filter': 'flat'},
    'battle': {'name': '⚔️ Battle Mode', 'desc': 'Music duels between users', 'filter': 'loud'}
}

equalizer_presets = {
    'bass': '-af "bass=g=15"',
    'treble': '-af "treble=g=12"',
    'flat': '',
    'loud': '-af "volume=2.0"',
    'nightcore': '-af "asetrate=48000*1.3,aresample=48000"',
    'slowed': '-af "asetrate=48000*0.75,aresample=48000"',
    'vaporwave': '-af "asetrate=48000*0.85,aresample=48000,bass=g=5"',
    'bassboost': '-af "bass=g=20,dynaudnorm"',
    '8d': '-af "apulsator=hz=0.09"',
    'echo': '-af "aecho=0.8:0.9:1000:0.3"',
    'flanger': '-af "flanger"',
    'phaser': '-af "aphaser=in_gain=0.4"',
    'robot': '-af "afftfilt=real=\'hypot(re,im)*sin((re+im)/2)\':imag=\'hypot(re,im)*cos((re+im)/2)\'"',
    'underwater': '-af "lowpass=f=300,highpass=f=100"',
    'radio': '-af "highpass=f=300,lowpass=f=3000, volume=1.5"',
    'megaphone': '-af "highpass=f=500,lowpass=f=4000, volume=2"',
    'chipmunk': '-af "asetrate=48000*1.5,aresample=48000"',
    'demon': '-af "asetrate=48000*0.6,aresample=48000"'
}

def load_data():
    global playlists, volumes, settings, stats, user_favorites, user_stats, radio_cache, song_relationships
    for file, storage in [(PLAYLIST_FILE, playlists), (VOLUME_FILE, volumes), 
                          (SETTINGS_FILE, settings), (STATS_FILE, stats),
                          (RADIO_FILE, radio_cache)]:
        if os.path.exists(file):
            with open(file, 'r') as f:
                storage.update(json.load(f))
    
    if os.path.exists(os.path.join(BOT_FOLDER, 'favorites.json')):
        with open(os.path.join(BOT_FOLDER, 'favorites.json'), 'r') as f:
            user_favorites.update(json.load(f))
    
    if os.path.exists(os.path.join(BOT_FOLDER, 'user_stats.json')):
        with open(os.path.join(BOT_FOLDER, 'user_stats.json'), 'r') as f:
            user_stats.update(json.load(f))
    
    if os.path.exists(os.path.join(BOT_FOLDER, 'relationships.json')):
        with open(os.path.join(BOT_FOLDER, 'relationships.json'), 'r') as f:
            song_relationships.update(json.load(f))

def save_data():
    for file, data in [(PLAYLIST_FILE, playlists), (VOLUME_FILE, volumes), 
                       (SETTINGS_FILE, settings), (STATS_FILE, stats),
                       (RADIO_FILE, radio_cache),
                       (os.path.join(BOT_FOLDER, 'favorites.json'), user_favorites),
                       (os.path.join(BOT_FOLDER, 'user_stats.json'), user_stats),
                       (os.path.join(BOT_FOLDER, 'relationships.json'), song_relationships)]:
        with open(file, 'w') as f:
            json.dump(data, f, indent=2)

load_data()

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5, filter_opts=''):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader', 'Unknown')
        self.view_count = data.get('view_count', 0)
        self.like_count = data.get('like_count', 0)
        self.filter_opts = filter_opts

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, volume=0.5, filter_opts=''):
        loop = loop or asyncio.get_event_loop()
        ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'ffmpeg_location': os.path.dirname(FFMPEG_PATH),
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_opts)
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        options = '-vn ' + filter_opts if filter_opts else '-vn'
        
        return cls(discord.FFmpegPCMAudio(
            filename, 
            executable=FFMPEG_PATH,
            options=options,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        ), data=data, volume=volume, filter_opts=filter_opts)

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

def create_progress_bar(current, total, length=20):
    if not total:
        return "▱" * length
    filled = int(length * current / total)
    return "▰" * filled + "▱" * (length - filled)

def get_similar_songs(song_title, artist=None, genre=None):
    """Generate similar song search queries based on current song"""
    similar_queries = []
    
    # Extract key info from title
    clean_title = re.sub(r'\([^)]*\)', '', song_title).strip()
    clean_title = re.sub(r'\[[^\]]*\]', '', clean_title).strip()
    
    # Strategy 1: Same artist different song
    if artist and artist != 'Unknown':
        similar_queries.append(f"{artist} best songs")
        similar_queries.append(f"{artist} popular")
    
    # Strategy 2: Same era/style based on keywords
    keywords = clean_title.lower().split()
    
    # Genre-based recommendations
    if genre:
        similar_queries.extend(GENRES.get(genre, [])[:2])
    
    # Mood-based from keywords
    mood_map = {
        'love': ['love songs', 'romantic hits', 'slow jams'],
        'night': ['night music', 'late night vibes', 'midnight'],
        'baby': ['r&b love songs', 'sweet songs', 'romantic'],
        'world': ['epic music', 'cinematic', 'world music'],
        'dance': ['dance hits', 'club music', 'party songs'],
        'heart': ['emotional songs', 'sad love songs', 'heartbreak'],
        'money': ['rap hits', 'hip hop', 'trap music'],
        'god': ['gospel', 'christian music', 'worship'],
        'summer': ['summer hits', 'beach music', 'tropical'],
        'winter': ['winter music', 'cozy', 'christmas'],
        'fire': ['fire songs', 'hype music', 'energy'],
        'water': ['chill music', 'ocean vibes', 'relaxing']
    }
    
    for keyword, queries in mood_map.items():
        if keyword in keywords:
            similar_queries.extend(queries)
    
    # Strategy 3: "More like this" patterns
    similar_patterns = [
        f"songs like {clean_title}",
        f"similar to {clean_title}",
        f"more {clean_title} style",
        f"artists similar to {artist if artist else clean_title}",
        f"if you like {clean_title}",
        f"{clean_title} type beat",
        f"music similar to {clean_title}",
        f"related to {clean_title}"
    ]
    similar_queries.extend(similar_patterns)
    
    # Strategy 4: Year/decade if detectable
    year_match = re.search(r'\b(19|20)\d{2}\b', song_title)
    if year_match:
        year = year_match.group()
        decade = year[:3] + '0s'
        similar_queries.append(f"{decade} hits")
        similar_queries.append(f"{year} music")
    
    # Strategy 5: Feature based
    if 'feat' in song_title.lower() or 'ft.' in song_title.lower():
        similar_queries.append('collaboration songs')
        similar_queries.append('featured artist hits')
    
    return list(set(similar_queries))  # Remove duplicates

def update_song_relationships(song1, song2):
    """Track that these songs are related"""
    key1 = song1.lower().strip()
    key2 = song2.lower().strip()
    
    if key1 not in song_relationships:
        song_relationships[key1] = []
    if key2 not in song_relationships[key1]:
        song_relationships[key1].append(key2)
    
    save_data()

@bot.event
async def on_ready():
    print(f'🎵 {bot.user} is online!')
    print(f'Loaded {len(GENRES)} genres, {len(MOODS)} moods, {len(equalizer_presets)} effects')
    
    bot.loop.create_task(status_loop())
    bot.loop.create_task(cleanup_sessions())
    bot.loop.create_task(auto_recommendation_loop())

async def status_loop():
    await bot.wait_until_ready()
    statuses = [
        discord.Activity(type=discord.ActivityType.listening, name="!help for commands"),
        discord.Activity(type=discord.ActivityType.playing, name=f"music in {len(bot.guilds)} servers"),
        discord.Activity(type=discord.ActivityType.watching, name="!similar for recommendations"),
        discord.Activity(type=discord.ActivityType.listening, name="!mode for special modes"),
        discord.Activity(type=discord.ActivityType.playing, name="!duel for music battles"),
    ]
    i = 0
    while not bot.is_closed():
        await bot.change_presence(activity=statuses[i % len(statuses)])
        i += 1
        await asyncio.sleep(15)

async def cleanup_sessions():
    while True:
        await asyncio.sleep(60)
        now = datetime.now()
        expired = [k for k, v in search_sessions.items() if now > v['expires']]
        for k in expired:
            del search_sessions[k]

async def auto_recommendation_loop():
    """Background task to auto-queue similar songs"""
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        for guild_id, session in list(radio_sessions.items()):
            if not session.get('active'):
                continue
            
            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue
            
            voice_client = guild.voice_client
            if not voice_client or not voice_client.is_playing():
                continue
            
            # Check if queue is low
            if guild_id not in queues or len(queues.get(guild_id, [])) < 2:
                # Add similar song
                current = current_players.get(guild_id)
                if current:
                    similar = get_similar_songs(current['title'], current.get('uploader'))
                    if similar:
                        query = random.choice(similar[:3])
                        # Silently add to queue
                        try:
                            ytdl = yt_dlp.YoutubeDL({
                                'format': 'bestaudio',
                                'quiet': True,
                                'ffmpeg_location': os.path.dirname(FFMPEG_PATH),
                            })
                            info = ytdl.extract_info(f"ytsearch:{query}", download=False)
                            if 'entries' in info and info['entries']:
                                entry = info['entries'][0]
                                if guild_id not in queues:
                                    queues[guild_id] = []
                                queues[guild_id].append({
                                    'url': entry['url'],
                                    'title': entry['title'],
                                    'requester': bot.user,
                                })
                        except:
                            pass

def get_volume(guild_id):
    return volumes.get(str(guild_id), 0.5)

def get_loop_mode(guild_id):
    return loop_modes.get(str(guild_id), 'off')

def get_filter(guild_id):
    if guild_id not in settings:
        return ''
    return settings[guild_id].get('filter', '')

async def play_next(ctx, loop_count=0):
    guild_id = str(ctx.guild.id)
    loop_mode = get_loop_mode(guild_id)
    
    if loop_mode == 'song' and guild_id in current_players and loop_count < 1:
        current = current_players[guild_id]
        await play_song_direct(ctx, current['url'], current['requester'], 
                              title=current.get('title'), silent=True, loop_count=loop_count+1)
        return
    
    if guild_id in queues and queues[guild_id]:
        next_song = queues[guild_id].pop(0)
        
        if loop_mode == 'queue':
            queues[guild_id].append(next_song)
        
        await play_song_direct(ctx, next_song['url'], next_song['requester'], 
                              title=next_song.get('title'), silent=True)
    else:
        current_players.pop(guild_id, None)
        await asyncio.sleep(300)
        if guild_id not in current_players and ctx.voice_client:
            await ctx.voice_client.disconnect()

async def play_song_direct(ctx, url, requester, title=None, silent=False, loop_count=0):
    guild_id = str(ctx.guild.id)
    
    if not os.path.exists(FFMPEG_PATH):
        if not silent:
            await ctx.send("❌ FFmpeg not found!", delete_after=5)
        return
    
    try:
        volume = get_volume(guild_id)
        filter_opts = get_filter(guild_id)
        
        # Check for special modes
        if guild_id in party_modes:
            mode = party_modes[guild_id]
            if mode.get('filter'):
                filter_opts = equalizer_presets.get(mode['filter'], '')
        
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True, volume=volume, filter_opts=filter_opts)
        
        actual_title = title or player.title
        
        def after_playing(error):
            if error:
                print(f"Error: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx, loop_count), bot.loop)
        
        ctx.voice_client.play(player, after=after_playing)
        
        current_players[guild_id] = {
            'title': actual_title,
            'requester': requester,
            'url': url,
            'started_at': datetime.now(),
            'duration': player.duration,
            'thumbnail': player.thumbnail,
            'uploader': player.uploader,
        }
        
        update_stats(str(requester.id), guild_id, actual_title)
        
        if guild_id not in song_history:
            song_history[guild_id] = []
        song_history[guild_id].append({
            'title': actual_title,
            'requester': requester.name,
            'time': datetime.now().isoformat()
        })
        if len(song_history[guild_id]) > 50:
            song_history[guild_id] = song_history[guild_id][-50:]
        
        if not silent:
            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"**[{actual_title}]({url})**",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Artist", value=player.uploader, inline=True)
            embed.add_field(name="⏱️ Duration", value=format_duration(player.duration), inline=True)
            embed.add_field(name="🔊 Volume", value=f"{int(volume*100)}%", inline=True)
            embed.add_field(name="🔁 Loop", value=get_loop_mode(guild_id).upper(), inline=True)
            embed.add_field(name="👀 Views", value=f"{player.view_count:,}" if player.view_count else "N/A", inline=True)
            embed.add_field(name="🎵 Requested by", value=requester.mention, inline=True)
            
            if player.thumbnail:
                embed.set_thumbnail(url=player.thumbnail)
            
            if filter_opts:
                filter_name = [k for k, v in equalizer_presets.items() if v == filter_opts]
                if filter_name:
                    embed.add_field(name="🎚️ Effect", value=filter_name[0].upper(), inline=False)
            
            # Add similar songs hint
            similar = get_similar_songs(actual_title, player.uploader)[:3]
            if similar:
                embed.add_field(name="🎯 Similar to this", value=" | ".join([f"`!play {s[:30]}`" for s in similar]), inline=False)
            
            embed.set_footer(text="Controls: ⏸️ Pause | ⏹️ Stop | ⏭️ Skip | 🔁 Loop | ❤️ Favorite | 🎯 Similar")
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction('⏸️')
            await msg.add_reaction('⏹️')
            await msg.add_reaction('⏭️')
            await msg.add_reaction('🔁')
            await msg.add_reaction('❤️')
            await msg.add_reaction('🎯')
            await msg.add_reaction('📥')
                
    except Exception as e:
        if not silent:
            await ctx.send(f"❌ Error: {str(e)[:200]}", delete_after=5)

async def search_and_play(ctx, query, is_radio=False):
    loading_msg = await ctx.send(f"🔍 Searching for: **{query}**...")
    
    try:
        ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': False,
            'ffmpeg_location': os.path.dirname(FFMPEG_PATH),
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_opts)
        search_query = f"ytsearch10:{query}"
        info = ytdl.extract_info(search_query, download=False)
        
        if 'entries' not in info or not info['entries']:
            await loading_msg.edit(content="❌ No results found!")
            await asyncio.sleep(3)
            await loading_msg.delete()
            return
        
        entries = info['entries'][:10]
        
        embed = discord.Embed(
            title="🎵 Search Results",
            description=f"Query: **{query}**\nReact to select:",
            color=discord.Color.blue()
        )
        
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Unknown')
            uploader = entry.get('uploader', 'Unknown')
            duration = format_duration(entry.get('duration'))
            views = entry.get('view_count', 0)
            
            embed.add_field(
                name=f"{emojis[i]} {title[:45]}{'...' if len(title) > 45 else ''}",
                value=f"👤 {uploader[:25]} | ⏱️ {duration} | 👀 {views:,}",
                inline=False
            )
        
        embed.set_footer(text="➕ = Add all | 🎲 = Random | 📻 = Radio | 🎯 = Similar | ❌ = Cancel")
        
        await loading_msg.delete()
        msg = await ctx.send(embed=embed)
        
        for i in range(len(entries)):
            await msg.add_reaction(emojis[i])
        await msg.add_reaction('➕')
        await msg.add_reaction('🎲')
        await msg.add_reaction('📻')
        await msg.add_reaction('🎯')
        await msg.add_reaction('❌')
        
        search_sessions[msg.id] = {
            'entries': entries,
            'ctx': ctx,
            'query': query,
            'expires': datetime.now() + timedelta(minutes=3),
            'is_radio': is_radio
        }
        
    except Exception as e:
        await loading_msg.edit(content=f"❌ Search error: {str(e)[:200]}")
        await asyncio.sleep(3)
        await loading_msg.delete()

# COMMANDS

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query):
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            msg = await ctx.send("❌ Join a voice channel first!", delete_after=5)
            return
    
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    is_url = bool(url_pattern.match(query))
    
    if is_url:
        await play_song_direct(ctx, query, ctx.author)
    else:
        await search_and_play(ctx, query)

@bot.command(name='similar', aliases=['like', 'related', 'more'])
async def similar_songs(ctx, *, song_query=None):
    """Find songs similar to current or specified song"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    # Use current song if no query
    if not song_query and guild_id in current_players:
        current = current_players[guild_id]
        song_query = current['title']
        artist = current.get('uploader', '')
    elif not song_query:
        await ctx.send("❌ Play a song or specify one! Example: `!similar Bohemian Rhapsody`", delete_after=5)
        return
    else:
        artist = None
    
    # Get similar queries
    similar = get_similar_songs(song_query, artist)
    
    if not similar:
        await ctx.send("❌ Couldn't find similar songs!", delete_after=5)
        return
    
    embed = discord.Embed(
        title=f"🎯 Songs Similar to: {song_query[:50]}",
        description="Click reactions or use commands:",
        color=discord.Color.gold()
    )
    
    # Show top 5 suggestions
    for i, suggestion in enumerate(similar[:5], 1):
        embed.add_field(name=f"{i}. {suggestion[:50]}", value=f"`!play {suggestion[:40]}`", inline=False)
    
    # Add auto-play option
    embed.set_footer(text="React: ▶️ = Play all similar | 🎲 = Random pick | 📻 = Radio mode")
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('▶️')
    await msg.add_reaction('🎲')
    await msg.add_reaction('📻')
    await msg.add_reaction('❌')
    
    # Store for reaction handling
    search_sessions[msg.id] = {
        'similar_queries': similar,
        'ctx': ctx,
        'song': song_query,
        'expires': datetime.now() + timedelta(minutes=2)
    }

@bot.command(name='radio', aliases=['r', 'autoplay', 'station'])
async def radio(ctx, *, query=None):
    """Smart radio - auto-finds similar songs forever"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    if not query and guild_id in current_players:
        query = current_players[guild_id]['title']
    elif not query:
        await ctx.send("❌ Play a song or specify seed! `!radio <song>`", delete_after=5)
        return
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    radio_sessions[guild_id] = {
        'seed': query,
        'active': True,
        'history': [],
        'user': ctx.author.id
    }
    
    await ctx.send(f"📻 **Smart Radio** started!\nSeed: **{query[:50]}**\nI'll auto-find similar songs forever! Use `!radiooff` to stop", delete_after=5)
    
    # Play seed song first
    await search_and_play(ctx, query, is_radio=True)

@bot.command(name='radiooff', aliases=['stopradio'])
async def radio_off(ctx):
    """Stop radio mode"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    if guild_id in radio_sessions:
        radio_sessions[guild_id]['active'] = False
        del radio_sessions[guild_id]
        await ctx.send("📻 Radio stopped!", delete_after=3)
    else:
        await ctx.send("📻 Radio wasn't on!", delete_after=3)

@bot.command(name='mode', aliases=['special', 'preset'])
async def special_mode(ctx, mode=None):
    """Special modes: focus/party/chill/workout/sleep/karaoke/battle"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    if not mode:
        embed = discord.Embed(title="🎛️ Special Modes", color=discord.Color.purple())
        for key, info in SPECIAL_MODES.items():
            embed.add_field(name=f"!mode {key}", value=f"{info['name']}\n{info['desc']}", inline=False)
        await ctx.send(embed=embed, delete_after=15)
        return
    
    mode = mode.lower()
    if mode not in SPECIAL_MODES:
        await ctx.send(f"❌ Mode not found! Use `!mode` to see options", delete_after=5)
        return
    
    if mode == 'battle':
        await ctx.send("⚔️ **Battle Mode**! Use `!duel @user` to start a music battle!", delete_after=5)
        return
    
    # Activate mode
    party_modes[guild_id] = SPECIAL_MODES[mode]
    
    # Apply settings
    if SPECIAL_MODES[mode].get('filter'):
        if guild_id not in settings:
            settings[guild_id] = {}
        settings[guild_id]['filter'] = equalizer_presets.get(SPECIAL_MODES[mode]['filter'], '')
        save_data()
    
    await ctx.send(f"{SPECIAL_MODES[mode]['name']} activated!\n{SPECIAL_MODES[mode]['desc']}", delete_after=5)

@bot.command(name='duel', aliases=['battle', 'vs'])
async def music_duel(ctx, opponent: discord.Member):
    """Music battle with another user"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    if opponent == ctx.author:
        await ctx.send("❌ Can't battle yourself!", delete_after=5)
        return
    
    if opponent.bot:
        await ctx.send("❌ Can't battle a bot!", delete_after=5)
        return
    
    guild_id = str(ctx.guild.id)
    
    duel_sessions[guild_id] = {
        'player1': ctx.author,
        'player2': opponent,
        'scores': {ctx.author.id: 0, opponent.id: 0},
        'round': 1,
        'songs': {ctx.author.id: None, opponent.id: None},
        'votes': {ctx.author.id: 0, opponent.id: 0}
    }
    
    embed = discord.Embed(
        title="⚔️ MUSIC DUEL!",
        description=f"{ctx.author.mention} VS {opponent.mention}\n\nRound 1: Pick your songs!",
        color=discord.Color.red()
    )
    embed.add_field(name="How to play:", value="1. Each player picks a song with `!play <song>`\n2. Server votes with reactions\n3. Winner gets point!\n4. Best of 3 rounds", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='time', aliases=['timeofday'])
async def time_playlist(ctx):
    """Play music based on current time"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        time_key = 'morning'
        emoji = '🌅'
    elif 12 <= hour < 17:
        time_key = 'afternoon'
        emoji = '☀️'
    elif 17 <= hour < 22:
        time_key = 'evening'
        emoji = '🌆'
    else:
        time_key = 'night'
        emoji = '🌙'
    
    query = random.choice(TIME_PLAYLISTS[time_key])
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    await ctx.send(f"{emoji} **{time_key.upper()}** Playlist - {query}", delete_after=3)
    await search_and_play(ctx, query)

@bot.command(name='weather', aliases=['w'])
async def weather_mode(ctx, condition=None):
    """Set weather mood: sunny/rainy/snowy/stormy/cloudy"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not condition:
        await ctx.send("🌤️ Use: `!weather sunny/rainy/snowy/stormy/cloudy`", delete_after=5)
        return
    
    condition = condition.lower()
    if condition not in WEATHER_MOODS:
        await ctx.send(f"❌ Options: {', '.join(WEATHER_MOODS.keys())}", delete_after=5)
        return
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    query = random.choice(WEATHER_MOODS[condition])
    await ctx.send(f"🌤️ **{condition.upper()}** Weather Vibes - {query}", delete_after=3)
    await search_and_play(ctx, query)

@bot.command(name='blend', aliases=['mix'])
async def blend_genres(ctx, genre1, genre2):
    """Blend two genres: !blend hip hop jazz"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    g1, g2 = genre1.lower(), genre2.lower()
    
    if g1 not in GENRES or g2 not in GENRES:
        await ctx.send(f"❌ Invalid genres! Use `!genre` to see list", delete_after=5)
        return
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    # Mix the genres
    mix_query = f"{g1} {g2} fusion" if random.random() > 0.5 else f"{g2} influenced {g1}"
    
    await ctx.send(f"🎨 Blending **{g1}** + **{g2}** = {mix_query}", delete_after=3)
    await search_and_play(ctx, mix_query)

@bot.command(name='surprise', aliases=['random', 'wtf'])
async def surprise_me(ctx):
    """Completely random song from anywhere"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    # Random combinations
    surprises = [
        'obscure 70s funk', 'rare jazz vinyl', 'underground rap 90s',
        'foreign language hit', 'one hit wonder', 'forgotten classic',
        'viral tiktok song', 'anime opening random', 'video game music',
        'movie soundtrack', 'tv show theme', 'commercial jingle',
        'weird experimental', 'unusual instrument', 'acapella cover',
        'live performance', 'unplugged version', 'remix random'
    ]
    
    query = random.choice(surprises)
    await ctx.send(f"🎲 **SURPRISE!** Playing: {query}", delete_after=3)
    await search_and_play(ctx, query)

@bot.command(name='challenge', aliases=['daily'])
async def daily_challenge(ctx):
    """Daily music challenge"""
    try:
        await ctx.message.delete()
    except:
        pass
    
    challenges = [
        ('Play a song from the year you were born', 'birthyear'),
        ('Play a song with a color in the title', 'color'),
        ('Play a song longer than 5 minutes', 'long'),
        ('Play a one-word title song', 'oneword'),
        ('Play a song from a movie', 'movie'),
        ('Play a song with "love" in title', 'love'),
        ('Play a song from a different continent', 'foreign'),
        ('Play the oldest song you know', 'old'),
        ('Play a song you hated but now like', 'guilty'),
        ('Play a song that tells a story', 'story')
    ]
    
    challenge, tag = random.choice(challenges)
    
    embed = discord.Embed(
        title="🎯 Daily Challenge",
        description=challenge,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Tag: #{tag} | Complete it with !play")
    
    await ctx.send(embed=embed)

@bot.command(name='genre')
async def genre_cmd(ctx, style=None):
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not style:
        embed = discord.Embed(title="🎸 All Genres", color=discord.Color.purple())
        genres_list = list(GENRES.keys())
        for i in range(0, len(genres_list), 4):
            row = genres_list[i:i+4]
            embed.add_field(name=" | ".join(row), value="\u200b", inline=False)
        await ctx.send(embed=embed, delete_after=15)
        return
    
    style = style.lower()
    if style not in GENRES:
        await ctx.send(f"❌ Not found! Use `!genre` to see list", delete_after=5)
        return
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    query = random.choice(GENRES[style])
    await ctx.send(f"🎸 **{style.upper()}** - {query}", delete_after=3)
    await search_and_play(ctx, query)

@bot.command(name='mood')
async def mood_cmd(ctx, feeling=None):
    try:
        await ctx.message.delete()
    except:
        pass
    
    if not feeling:
        embed = discord.Embed(title="🎭 All Moods", color=discord.Color.orange())
        moods_text = " | ".join([f"`{m}`" for m in MOODS.keys()])
        embed.description = moods_text
        await ctx.send(embed=embed, delete_after=15)
        return
    
    feeling = feeling.lower()
    if feeling not in MOODS:
        await ctx.send(f"❌ Not found! Use `!mood` to see list", delete_after=5)
        return
    
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Join voice first!", delete_after=5)
            return
    
    query = random.choice(MOODS[feeling])
    await ctx.send(f"🎭 **{feeling.upper()}** - {query}", delete_after=3)
    await search_and_play(ctx, query)

@bot.command(name='eq')
async def equalizer_cmd(ctx, preset=None):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    if not preset:
        embed = discord.Embed(title="🎚️ Audio Effects", color=discord.Color.blue())
        effects = [("bass", "Boost bass"), ("treble", "Boost treble"), ("nightcore", "Speed up"),
                   ("slowed", "Slow + reverb"), ("vaporwave", "Aesthetic"), ("bassboost", "Extreme bass"),
                   ("8d", "8D audio"), ("echo", "Echo"), ("flanger", "Flanger"), ("robot", "Robot voice"),
                   ("underwater", "Underwater"), ("radio", "Radio quality"), ("megaphone", "Megaphone"),
                   ("chipmunk", "Chipmunk"), ("demon", "Demon voice"), ("flat", "No effect")]
        for name, desc in effects:
            embed.add_field(name=f"!eq {name}", value=desc, inline=True)
        await ctx.send(embed=embed, delete_after=15)
        return
    
    preset = preset.lower()
    if preset not in equalizer_presets:
        await ctx.send("❌ Invalid effect!", delete_after=5)
        return
    
    if guild_id not in settings:
        settings[guild_id] = {}
    settings[guild_id]['filter'] = equalizer_presets[preset]
    save_data()
    
    await ctx.send(f"🎚️ **{preset.upper()}** enabled!", delete_after=3)

@bot.command(name='volume', aliases=['vol'])
async def volume(ctx, vol=None):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    if vol is None:
        current = int(get_volume(guild_id) * 100)
        await ctx.send(f"🔊 Volume: **{current}%**", delete_after=5)
        return
    
    try:
        vol = int(vol)
        if vol < 0 or vol > 200:
            await ctx.send("❌ 0-200%", delete_after=5)
            return
        
        volumes[guild_id] = vol / 100
        save_data()
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = vol / 100
        
        await ctx.send(f"🔊 Volume: **{vol}%**", delete_after=3)
    except:
        await ctx.send("❌ Invalid!", delete_after=5)

@bot.command(name='loop')
async def loop(ctx, mode=None):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    if not mode:
        current = get_loop_mode(guild_id)
        await ctx.send(f"🔁 Loop: **{current.upper()}**", delete_after=5)
        return
    
    mode = mode.lower()
    if mode not in ['off', 'song', 'queue']:
        await ctx.send("❌ off/song/queue", delete_after=5)
        return
    
    loop_modes[guild_id] = mode
    await ctx.send(f"🔁 Loop: **{mode.upper()}**", delete_after=3)

@bot.command(name='skip')
async def skip(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!", delete_after=2)
    else:
        await ctx.send("❌ Nothing!", delete_after=5)

@bot.command(name='queue', aliases=['q'])
async def show_queue(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    
    embed = discord.Embed(title="📋 Queue", color=discord.Color.purple())
    
    if guild_id in current_players:
        song = current_players[guild_id]
        elapsed = (datetime.now() - song['started_at']).seconds if isinstance(song['started_at'], datetime) else 0
        bar = create_progress_bar(elapsed, song.get('duration', 0))
        embed.add_field(name="🎶 Now Playing", value=f"**{song['title'][:60]}**\n{bar}", inline=False)
    
    if guild_id in queues and queues[guild_id]:
        text = ""
        for i, song in enumerate(queues[guild_id][:10], 1):
            text += f"`{i}.` {song['title'][:40]}\n"
        embed.add_field(name=f"Up Next ({len(queues[guild_id])})", value=text, inline=False)
    else:
        embed.add_field(name="Up Next", value="Empty", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='clear')
async def clear_queue(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    if guild_id in queues:
        queues[guild_id] = []
    await ctx.send("🗑️ Cleared!", delete_after=3)

@bot.command(name='join')
async def join(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("✅ Joined!", delete_after=3)
    else:
        await ctx.send("❌ Join voice!", delete_after=5)

@bot.command(name='leave')
async def leave(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    guild_id = str(ctx.guild.id)
    if guild_id in queues:
        queues[guild_id] = []
    current_players.pop(guild_id, None)
    
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left!", delete_after=3)

@bot.command(name='help')
async def help_cmd(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    embed = discord.Embed(title="🎵 Music Bot - Ultimate Edition", color=discord.Color.blue())
    
    categories = {
        "🎶 Smart Play": ["`!play <song>` - Search & play", "`!similar` - Find similar songs", "`!radio <song>` - Auto-radio forever", "`!recommend` - Smart recommendations"],
        "🎛️ Modes": ["`!mode focus/party/chill/workout/sleep/karaoke/battle` - Special modes", "`!duel @user` - Music battle", "`!time` - Time-based playlist", "`!weather <condition>` - Weather vibes"],
        "🎸 Genres & Moods": ["`!genre <style>` - 30+ genres", "`!mood <feeling>` - 12 moods", "`!blend <g1> <g2>` - Mix genres", "`!top global/usa/uk/viral` - Charts"],
        "🎚️ Effects": ["`!eq <effect>` - 16 audio effects", "`!volume <0-200>` - Volume", "`!loop off/song/queue` - Loop"],
        "🎯 Fun": ["`!surprise` - Random song", "`!discover` - New music", "`!challenge` - Daily challenge", "`!trending` - Viral hits", "`!decade <year>` - Era music"],
        "📋 Queue": ["`!queue` - Show queue", "`!skip` - Skip", "`!clear` - Clear", "`!join/!leave` - Connect"]
    }
    
    for cat, cmds in categories.items():
        embed.add_field(name=cat, value="\n".join(cmds), inline=False)
    
    embed.set_footer(text="All commands auto-delete | Smart radio finds similar songs automatically!")
    await ctx.send(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    msg_id = reaction.message.id
    
    if msg_id not in search_sessions:
        # Player controls
        if reaction.emoji in ['⏸️', '⏹️', '⏭️', '🔁', '❤️', '📥', '🎯']:
            ctx = await bot.get_context(reaction.message)
            guild_id = str(reaction.message.guild.id)
            
            if reaction.emoji == '🎯':
                # Trigger similar songs
                if guild_id in current_players:
                    current = current_players[guild_id]
                    similar = get_similar_songs(current['title'], current.get('uploader'))
                    if similar:
                        query = random.choice(similar[:3])
                        await ctx.send(f"🎯 Playing similar: **{query[:50]}**", delete_after=3)
                        await play_song_direct(ctx, query, user, title=query)
                return
            
            if reaction.emoji == '⏸️':
                if ctx.voice_client:
                    if ctx.voice_client.is_playing():
                        ctx.voice_client.pause()
                    elif ctx.voice_client.is_paused():
                        ctx.voice_client.resume()
            elif reaction.emoji == '⏹️':
                if guild_id in queues:
                    queues[guild_id] = []
                if ctx.voice_client:
                    ctx.voice_client.stop()
                current_players.pop(guild_id, None)
            elif reaction.emoji == '⏭️':
                if ctx.voice_client:
                    ctx.voice_client.stop()
            elif reaction.emoji == '🔁':
                current = get_loop_mode(guild_id)
                modes = ['off', 'song', 'queue']
                next_mode = modes[(modes.index(current) + 1) % 3]
                loop_modes[guild_id] = next_mode
                await ctx.send(f"🔁 Loop: **{next_mode.upper()}**", delete_after=3)
            elif reaction.emoji == '❤️':
                if guild_id in current_players:
                    song = current_players[guild_id]
                    uid = str(user.id)
                    if uid not in user_favorites:
                        user_favorites[uid] = []
                    if not any(f['title'] == song['title'] for f in user_favorites[uid]):
                        user_favorites[uid].append({
                            'title': song['title'],
                            'url': song['url'],
                            'added_at': datetime.now().isoformat()
                        })
                        save_data()
                        await ctx.send(f"❤️ {user.mention} favorited!", delete_after=3)
        return
    
    session = search_sessions[msg_id]
    if datetime.now() > session['expires']:
        del search_sessions[msg_id]
        return
    
    ctx = session['ctx']
    emoji = str(reaction.emoji)
    
    # Handle similar songs menu
    if 'similar_queries' in session:
        similar = session['similar_queries']
        
        if emoji == '▶️':
            # Play all similar
            for query in similar[:3]:
                await play_song_direct(ctx, query, user, title=query, silent=True)
            await ctx.send(f"▶️ Added {len(similar[:3])} similar songs!", delete_after=3)
        elif emoji == '🎲':
            # Random pick
            query = random.choice(similar)
            await play_song_direct(ctx, query, user, title=query)
        elif emoji == '📻':
            # Radio mode
            radio_sessions[str(ctx.guild.id)] = {'seed': session['song'], 'active': True}
            await ctx.send(f"📻 Radio based on **{session['song'][:40]}**", delete_after=3)
        
        del search_sessions[msg_id]
        try:
            await reaction.message.delete()
        except:
            pass
        return
    
    # Regular search menu
    entries = session['entries']
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    if emoji == '❌':
        await ctx.send("❌ Cancelled", delete_after=2)
        del search_sessions[msg_id]
        try:
            await reaction.message.delete()
        except:
            pass
        return
    
    if emoji == '➕':
        for entry in entries:
            await play_song_direct(ctx, entry['url'], user, title=entry.get('title'), silent=True)
        await ctx.send(f"✅ Added all!", delete_after=3)
    elif emoji == '🎲':
        selected = random.choice(entries)
        await play_song_direct(ctx, selected['url'], user, title=selected.get('title'))
    elif emoji == '📻':
        radio_sessions[str(ctx.guild.id)] = {'seed': session['query'], 'active': True}
        await ctx.send(f"📻 Radio mode!", delete_after=3)
        return
    elif emoji == '🎯':
        # Find similar to selected
        selected = entries[0]  # Default to first
        similar = get_similar_songs(selected.get('title'), selected.get('uploader'))
        if similar:
            query = random.choice(similar[:3])
            await ctx.send(f"🎯 Similar: **{query[:50]}**", delete_after=3)
            await play_song_direct(ctx, query, user, title=query)
        return
    
    if emoji in emojis:
        index = emojis.index(emoji)
        if index < len(entries):
            selected = entries[index]
            if not ctx.voice_client:
                if ctx.author.voice:
                    await ctx.author.voice.channel.connect()
            await play_song_direct(ctx, selected['url'], user, title=selected.get('title'))
            
            # Store relationship for future recommendations
            for other in entries[:3]:
                if other != selected:
                    update_song_relationships(selected.get('title'), other.get('title'))
    
    del search_sessions[msg_id]
    try:
        await reaction.message.delete()
    except:
        pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.name and 'playlist' in message.channel.name.lower():
        content = message.content.strip()
        if content.startswith('!'):
            await bot.process_commands(message)
            return
        
        if message.author.voice and content:
            ctx = await bot.get_context(message)
            if ctx.voice_client is None:
                await message.author.voice.channel.connect()
            try:
                await message.delete()
            except:
                pass
            await search_and_play(ctx, content)
            return
    
    await bot.process_commands(message)

# Keep-alive for Render.com (optional but recommended)
from aiohttp import web

async def health_check(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', health_check)

async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

# Run both bot and web server
async def main():
    await asyncio.gather(
        start_web_server(),
        bot.start(os.getenv('DISCORD_TOKEN'))
    )

if __name__ == "__main__":
    asyncio.run(main())