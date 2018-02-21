#BOT MADE BY MDOP
import os
import sys
import time
import shlex
import shutil
import random
import asyncio
import discord
import inspect
import logging
import pathlib
import traceback
import math
import re
from discord.ext import commands
if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

def __init__(self, bot):
        self.bot = bot
class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = ' {0.title}' #uploaded by {0.uploader}  and requested by {1.display_name}
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() 
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            embed=discord.Embed(color=0xf807f8)
            embed.add_field(name="Now playing:", value=""+ str(self.current), inline=True)
            await self.bot.send_message(self.current.channel, embed=embed)
            await self.bot.change_presence(game=discord.Game(name=""+ str(self.current)))
            self.current.player.start()
            await self.play_next_song.wait()
class Music:
 
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Does nothing :D"""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in **' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Joins bot to channel..."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('Are you sure your in a channel?')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Finds and plays ur song..."""
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            embed=discord.Embed(color=0x3401fe)
            embed.add_field(name="Loading the song please be patient...", value="=========================", inline=True)
            await self.bot.say(embed=embed)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            embed=discord.Embed(color=0xf807f8)
            embed.add_field(name="Enqueued:", value=""+ str(entry), inline=True)
            await self.bot.say(embed=embed)
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets volume to current song..."""
        state = self.get_voice_state(ctx.message.server)
        if (state.is_playing() and value <= 100):
            player = state.player
            player.volume = value / 100
            embed=discord.Embed(color=0x00ff40)
            embed.set_footer(text='Set the volume to {:.0%}'.format(player.volume))
            await self.bot.say(embed=embed)

        else:

            if (state.is_playing() and value > 100):
                embed=discord.Embed(color=0x00ff40)
                embed.set_footer(text="Max volume is 100%")
                await self.bot.say(embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes song..."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Disconnects bot from channel and stops song..."""
        server = ctx.message.server
        state = self.get_voice_state(server)
        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
            embed=discord.Embed(color=0xff0600)
            embed.set_footer(text="Cleared the queue and disconnected from voice channel ")
            await self.bot.say(embed=embed)
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Skips song..."""
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            embed=discord.Embed(color=0x00ff40)
            embed.set_footer(text="Not playing any music right now...")
            await self.bot.say(embed=embed)
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            embed=discord.Embed(color=0x00ff40)
            embed.set_footer(text="Requester requested skipping song...")
            await self.bot.say(embed=embed)
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 1:
                embed=discord.Embed(color=0xf807f8)
                embed.set_footer(text="Skip vote passed, skipping song...")
                await self.bot.say(embed=embed)
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/1]'.format(total_votes))
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            embed=discord.Embed(color=0xf807f8)
            embed.set_footer(text="Now playing {} [skips: {}/1]".format(state.current, skip_count))
            await self.bot.say(embed=embed)
            await asyncio.sleep(10)
            await self.bot.message_delete(embed=embed)

def setup(bot):
    bot.add_cog(Music(bot))
    print('.............MUSIC BOT IS READY..............')