
#===============================================================================================
#===============================================================================================
#IMPORTS
#===============================================================================================
#===============================================================================================

import discord
import asyncio
import string
import json
import requests
import os
import io
import sqlite3
import datetime as DT
import random
import interactions
from youtube_dl import YoutubeDL
from io import BytesIO
from asyncio import sleep
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw
from discord import guild, member
from discord_slash import SlashCommand, SlashContext
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption

#===============================================================================================
#===============================================================================================
#CLIENT
#===============================================================================================
#===============================================================================================
async def get_prefix(client, message):
	cursor.execute(f"SELECT prefix FROM guilds WHERE guild_id = '{message.guild.id}'")
	prefix = cursor.fetchone()
	connection.commit

	return prefix

intents = discord.Intents().default()
client = commands.Bot(command_prefix=get_prefix, help_command=None, intents=intents)
slash = SlashCommand(client, sync_commands=True)

connection = sqlite3.connect('sample.db')
cursor = connection.cursor()

#===============================================================================================
#===============================================================================================
#EVENTS
#===============================================================================================
#===============================================================================================

@client.event
async def on_ready():
	DiscordComponents(client)
	print("Привет! Бот успешно запущен!")
	await client.change_presence(status=discord.Status.idle, activity=discord.Game("тетрис | .хелп"))

	cursor.execute("""CREATE TABLE IF NOT EXISTS guilds(
		guild_id TEXT,
		prefix TEXT
	)""")

	for guild in client.guilds:
		if cursor.execute(f"SELECT prefix FROM guilds WHERE guild_id = {guild.id}").fetchone() is None:
			cursor.execute(f"INSERT INTO guilds VALUES ('{guild.id}', '.')")
		else:
			pass

	connection.commit()

@client.event
async def on_guild_join(guild):
	cursor.execute(f"INSERT INTO guilds VALUES ('{guild.id}', '.')")
	connection.commit()

	print(f"[logs] (event) Бот был добавлен на сервер {guild.name}")

@client.event
async def on_guild_remove(guild):
	cursor.execute(f"DELETE FROM guilds WHERE guild_id = {guild.id}")
	connection.commit()

	print(f"[logs] (event) Бот был удалён с сервера {guild.name}")

#===============================================================================================
#===============================================================================================
#COMMANDS
#===============================================================================================
#===============================================================================================

#===============================================================================================
#SETTINGS
#===============================================================================================
@client.command()
@commands.is_owner()
async def setprefix(ctx, prefix):
	cursor.execute(f"UPDATE guilds SET prefix = '{prefix}' WHERE guild_id = '{ctx.guild.id}'")
	connection.commit()
	embed=discord.Embed(title="Успешно", description=f"Префикс изменён на {prefix}")
	await ctx.send(embed=embed)

	print(f"[logs] На сервере {ctx.guild.name} изменён префикс на {prefix} | .setprefix")

#===============================================================================================
#ECONOMY
#===============================================================================================

@client.command()
async def ping(ctx):
	await ctx.send(embed=discord.Embed(title="Pong!", description=f"Задержка: `{client.ws.latency * 1000:.0f}ms`", color=discord.Color.magenta()))

	print("[logs] Была использована команда .ping")

@client.command(aliases = ['help', 'хелп'])
async def __help(ctx):
	embed = discord.Embed(title="Полный список команд.", color=discord.Color.magenta())
	embed.add_field(name="🛡 Модерация", value="`.кик` `.бан` `.разбан` `.мут` `.размут` `.очистить`", inline=False)

	#set_footer(text="В скором времени будет добавлено больше команд!", icon_url="https://cdn.discordapp.com/attachments/937064671343689779/938385378942025728/ball.gif")

	msg = await ctx.send(
		embed=embed,
		components = [
			Select(
				placeholder = "Выберите категорию",
				custom_id = "helpcommand",
				options = [
					SelectOption(label = "Модерация", value = "mod", emoji = "🛡"),
				]
			)
		]
	)

#===============================================================================================
#MODERATION
#===============================================================================================

#==========KICK COMMAND==========
@client.command(aliases = ['kick', 'кик'])
@commands.has_permissions(kick_members = True)
async def __kick(ctx, member: discord.Member, *, reason = None):
	embedm = discord.Embed(title="Вы были исключены!", color=discord.Color.red())
	embedm.add_field(name="Модератор:", value=ctx.author.mention)
	embedm.add_field(name="Причина:", value=reason)
	await member.send(embed=embedm)

	embed=discord.Embed(title="Успешно!", color=discord.Color.green())
	await ctx.send(embed=embed)
	await member.kick(reason=reason)

	print(f"[logs] Был исключён участник {member} по причине {reason}. | .kick")

@__kick.error
async def kick_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="Недостаточно аргументов.", color=discord.Color.red())
		embed.add_field(name="Использование:", value="`.кик < @Участник | ID >`", inline=False)
		await ctx.send(embed=embed)

		print("[logs] (error) Необходимо указать учатника. | .kick")
	if isinstance(error, commands.MissingPermissions):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="У вас недостаточно прав для выполнения этой команды.", color=discord.Color.red())
		await ctx.send(embed=embed)

		print(f"[logs] (error) У пользователя {ctx.author} недостаточно прав. | .kick")

#==========BAN COMMAND==========
@client.command(aliases = ['ban', 'бан'])
@commands.has_permissions(ban_members = True)
async def __ban(ctx, member: discord.Member, *, reason = None):
	embedm = discord.Embed(title="Вы были забанены!", color=discord.Color.red())
	embedm.add_field(name="Модератор:", value=ctx.author.mention)
	embedm.add_field(name="Причина:", value=reason)
	await member.send(embed=embedm)

	embed = discord.Embed(title="Успешно!", color=discord.Color.green())
	await ctx.send(embed=embed)
	await member.ban(reason=reason)

	print(f"[logs] Был забанен участник {member} по причине {reason}. | .ban")

@__ban.error
async def ban_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="Недостаточно аргументов.", color=discord.Color.red())
		embed.add_field(name="Использование:", value="`.бан < @Участник | ID > [Причина]`", inline=False)
		await ctx.send(embed=embed)

		print("[logs] (error) Необходимо указать учатника. | .ban")
	if isinstance(error, commands.MissingPermissions):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="У вас недостаточно прав для выполнения этой команды.", color=discord.Color.red())
		await ctx.send(embed=embed)

		print(f"[logs] (error) У пользователя {ctx.author} недостаточно прав. | .ban")

#==========UNBAN COMMAND==========
@client.command(aliases = ['unban', 'разбан'])
@commands.has_permissions(ban_members=True)
async def __unban(ctx, *, member):
	banned_users = await ctx.guild.bans()
	member_name, member_discriminator = member.split('#')
	for ban_entry in banned_users:
		user = ban_entry.user
		if (user.name, user.discriminator) == (member_name, member_discriminator):
			await ctx.guild.unban(user)
			await ctx.send(embed=discord.Embed(title="Успешно!", description=f"Пользователь {user} был разбанен.", color=discord.Color.green()))

			print(f"{ctx.author} разбанил {user}. | .unban")

@__unban.error
async def unban_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="Недостаточно аргументов.", color=discord.Color.red())
		embed.add_field(name="Использование:", value="`.разбан < участник#1234 >`", inline=False)
		await ctx.send(embed=embed)

		print("[logs] (error) Необходимо указать учатника. | .unban")
	if isinstance(error, commands.MissingPermissions):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="У вас недостаточно прав для выполнения этой команды.", color=discord.Color.red())
		await ctx.send(embed=embed)

		print(f"[logs] (error) У пользователя {ctx.author} недостаточно прав. | .unban")

#==========CLEAR COMMAND==========
@client.command(aliases = ['clear', 'очистить'])
@commands.has_permissions(manage_messages = True)
async def __clear(ctx, amount: int):
	await ctx.channel.purge(limit=1)
	await ctx.channel.purge(limit=amount)
	await ctx.send(embed=discord.Embed(title="Успешно!", description=f"Удалено сообщений: {amount}", color=discord.Color.green()))

	print(f"[logs] Участник {ctx.author} удалил {amount} сообщений. | .clear")

@__clear.error
async def clear_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="Недостаточно аргументов.", color=discord.Color.red())
		embed.add_field(name="Использование:", value="`.очистить < Кол-во сообщений >`", inline=False)
		await ctx.send(embed=embed)

		print("[logs] (error) Необходимо указать кол-во сообщений. | .clear")
	if isinstance(error, commands.MissingPermissions):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="У вас недостаточно прав для выполнения этой команды.", color=discord.Color.red())
		await ctx.send(embed=embed)

		print(f"[logs] (error) У пользователя {ctx.author} недостаточно прав. | .clear")

#==========MUTE COMMAND==========
@client.command(aliases = ['mute', 'мут'])
@commands.has_permissions(manage_messages = True)
async def __mute(ctx, member: discord.Member, amount_time):

	if 'м' in amount_time:
		embed2=discord.Embed(title="Успешно!", description=f"Участник {member.mention} был замьючен на {amount_time}",color=discord.Color.green())
		msg = await ctx.reply(embed=embed2)
 
		mute_role = discord.utils.get(ctx.guild.roles, id = 945753144003018762)
		await member.add_roles(mute_role)
		print(f"[logs] {ctx.author} замьютил {member} на {amount_time} | .mute")
		await asyncio.sleep(int(amount_time[:-1]) * 60)
		await member.remove_roles(mute_role)
 
		embed1 = discord.Embed(description = f'Время мута {member.mention} истекло. С него была снята роль мута.', color=discord.Color.green())
		await msg.reply(embed=embed1)

		print(f"[logs] Время мута {member} истекло | .mute")
	elif 'ч' in amount_time:
		embed2=discord.Embed(title="Успешно!", description=f"Участник {member.mention} был замьючен на {amount_time}",color=discord.Color.green())
		await ctx.reply(embed=embed2)

		mute_role = discord.utils.get(ctx.guild.roles, id = 945753144003018762)
		await member.add_roles(mute_role)
		print(f"[logs] {ctx.author} замьютил {member} на {amount_time} | .mute")
		await asyncio.sleep(int(amount_time[:-1]) * 60 * 60)
		await member.remove_roles(mute_role)
 
		embed1 = discord.Embed(description = f'Время мута {member.mention} истекло. С него была снята роль мута.', color=discord.Color.green())
		await ctx.reply(embed=embed1)

		print(f"[logs] Время мута {member} истекло | .mute")
	elif 'д' in amount_time:
		embed2=discord.Embed(title="Успешно!", description=f"Участник {member.mention} был замьючен на {amount_time}",color=discord.Color.green())
		await ctx.reply(embed=embed2)
 
		mute_role = discord.utils.get(ctx.guild, id = 945753144003018762)
		await member.add_roles(mute_role)
		print(f"[logs] {ctx.author} замьютил {member} на {amount_time} | .mute")
		await asyncio.sleep(int(amount_time[:-1]) * 60 * 60 * 24)
		await member.remove_roles(mute_role)
 
		embed1 = discord.Embed(description = f'Время мута {member.mention} истекло. С него была снята роль мута.', color=discord.Color.green())
		await ctx.reply(embed=embed1)

		print(f"[logs] Время мута {member} истекло | .mute")
	elif 'с' in amount_time:
		embed2=discord.Embed(title="Успешно!", description=f"Участник {member.mention} был замьючен на {amount_time}",color=discord.Color.green())
		msg = await ctx.reply(embed=embed2)
 
		mute_role = discord.utils.get(ctx.guild.roles, id = 945753144003018762)
		await member.add_roles(mute_role)
		print(f"[logs] {ctx.author} замьютил {member} на {amount_time} | .mute")
		await asyncio.sleep(int(amount_time[:-1]))
		await member.remove_roles(mute_role)
 
		embed1 = discord.Embed(description = f'Время мута {member.mention} истекло. С него была снята роль мута.', color=discord.Color.green())
		await msg.reply(embed=embed1)

		print(f"[logs] Время мута {member} истекло | .mute")

@__mute.error
async def mute_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="Недостаточно аргументов.", color=discord.Color.red())
		embed.add_field(name="Использование:", value="`.мут < @Участник | ID > < Время мута с/м/ч/д >`", inline=False)
		embed.add_field(name="Памятка:", value="`с = секунды` / `м = минуты` / `ч = часы` / `д = дни`")
		await ctx.send(embed=embed)

		print("[logs] (error) Необходимо указать участника / время мута. | .mute")
	if isinstance(error, commands.MissingPermissions):
		embed = discord.Embed(title="Ошибка в использовании команды.", description="У вас недостаточно прав для выполнения этой команды.", color=discord.Color.red())
		await ctx.send(embed=embed)

		print(f"[logs] (error) У пользователя {ctx.author} недостаточно прав. | .mute")

#==========UNMUTE COMMAND==========
@client.command(aliases = ['unmute', 'размут'])
@commands.has_permissions(manage_messages = True)
async def __unmute(ctx, member: discord.Member):
	mute_role = discord.utils.get(ctx.guild.roles, id = 945753144003018762)
	await member.remove_roles(mute_role)

	await ctx.send(embed=discord.Embed(title="Успешно!", description=f"С участника {member.mention} был снят мут.",color=discord.Color.green()))

#===============================================================================================
#===============================================================================================
#RUN
#===============================================================================================
#===============================================================================================

client.run("OTQ1NjY4NDM3MzQ1MjA2MzUz.YhTgXQ.tqhZF89QUhmZoxgYXRmdPuTivAs")