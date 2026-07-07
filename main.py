import disnake
from disnake.ext import commands
import os
import asyncio
from disnake.enums import ButtonStyle
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import pytz
from disnake import Webhook
import json
import config

client = commands.Bot(command_prefix = '!', intents=disnake.Intents.all(), test_guilds=[config.TEST_GUILDS[0]])
client.remove_command('help')
kick_counter = defaultdict(int)
user_ids = []
klever = config.OWNER_ID
admins = config.ADMIN_IDS

# ================================================================================================ #

@client.event
async def on_ready():
    await client.change_presence(status=disnake.Status.do_not_disturb, activity=disnake.Activity(type=disnake.ActivityType.watching, name="admin abusers"))
    print(f'Logged in as {client.user}')

# ================================================================================================ #

@client.event
async def on_guild_channel_create(channel):
    log_channel = client.get_channel(config.LOG_CHANNELS["channel_create"])
    creator = None
    created_at = channel.created_at
    guild = channel.guild
    
    async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_create):
        if entry.created_at >= created_at:
            creator = entry.user
            
    quarantine = disnake.utils.get(channel.guild.roles, id=config.ROLES["quarantine"])
    DVP = disnake.utils.get(channel.guild.roles, id=config.ROLES["dvp"])
    AI = disnake.utils.get(channel.guild.roles, id=config.ROLES["ai"])
    server_booster = disnake.utils.get(channel.guild.roles, id=config.ROLES["server_booster"])
    channel_create_history = await channel.guild.audit_logs(limit=20, action=disnake.AuditLogAction.channel_create).filter(lambda e: e.user == creator and e.created_at > channel.created_at - timedelta(minutes=30)).flatten()
    channels_created = len(channel_create_history)
    
    embed = disnake.Embed(
            title="Punishment Issued",
            description=f"{creator.mention} Received Quarantine role for creating `{channels_created}` channels in `30` minutes.",
            color=disnake.Color.red()
        )
    embed.set_thumbnail(url = creator.avatar)
    embed2 = disnake.Embed(
            title="Channel Creation",
            description=f"New channel {channel.mention} created by - {creator.mention}",
            color=disnake.Color.green()
        )
    embed2.set_thumbnail(url = creator.avatar)
    embed3 = disnake.Embed(
            title="Warning",
            description=f"New channel created by bot - {creator.mention}.\n`Channels deleted, bot banned.`",
            color=disnake.Color.red()
        )
    if creator.bot:
        member = guild.get_member(creator.id)
        if member and any(role.id == config.ROLES["ai"] for role in member.roles):
            if log_channel != None:
                await log_channel.send(embed=embed2)
            return
        else:
            await guild.ban(creator, reason="Bot banned for unauthorized actions.")
            if log_channel != None:
                await log_channel.send(embed=embed3)
            await channel.delete()
            return

    else:
        if channels_created >= 1 and not DVP in creator.roles and not AI in creator.roles:
            if any(role.id == config.ROLES["server_booster"] for role in creator.roles):
                    roles_to_add = [quarantine,server_booster]
            else:
                    roles_to_add = [quarantine]
            try:
                await creator.edit(roles=roles_to_add, reason="User exceeded channel creation limit.") 
            except:
                print(f'{creator.id}')
                pass
            if log_channel !=None:
                await log_channel.send(embed=embed)
            await channel.delete()
        else:
            if log_channel !=None:
                await log_channel.send(embed=embed2)

# ================================================================================================ #

@client.event
async def on_guild_channel_delete(channel):    
    log_channel = client.get_channel(config.LOG_CHANNELS["channel_delete"])
    guild = channel.guild
    async for entry in channel.guild.audit_logs(limit=1):
        if entry.target.id == channel.id:
            deleter = entry.user
        break
    guild = channel.guild
    quarantine = disnake.utils.get(channel.guild.roles, id=config.ROLES["quarantine"])
    DVP = disnake.utils.get(channel.guild.roles, id=config.ROLES["dvp"])
    AI = disnake.utils.get(channel.guild.roles, id=config.ROLES["ai"])
    server_booster = disnake.utils.get(channel.guild.roles, id=config.ROLES["server_booster"])
    
    deleter = entry.user
    
    channel_delete_history = await channel.guild.audit_logs(limit=20, action=disnake.AuditLogAction.channel_delete).filter(lambda e: e.user == deleter and e.created_at > channel.created_at - timedelta(minutes=30)).flatten()
    channels_deleted = len(channel_delete_history)
    embed = disnake.Embed(
            title="Punishment Issued",
            description=f"{deleter.mention} received role Quarantine for deleting `{channels_deleted}` channels in `30` minutes.",
            color=disnake.Color.red()
        )
    embed.set_thumbnail(url = deleter.avatar)
    embed2 = disnake.Embed(
            title="Channel Deletion",
            description=f"Channel `{channel.name}` was deleted by - {deleter.mention}.",
            color=disnake.Color.green()
        )
    embed2.set_thumbnail(url = deleter.avatar)
    embed3 = disnake.Embed(
            title="Attention",
            description=f"Bot deleted a channel and was banned: {deleter.mention}.",
            color=disnake.Color.red()
        )
    embed3.set_thumbnail(url = deleter.avatar)

    if deleter.bot:
        member = guild.get_member(deleter.id)
        if member and any(role.id == config.ROLES["ai"] for role in member.roles):
            try:
                await log_channel.send(embed=embed2)
            except AttributeError:
                pass
        else:
            await guild.ban(deleter, reason="Bot banned for unauthorized actions.")
            try:
                await log_channel.send(embed=embed3)
            except AttributeError:
                pass
            
    else:
        if channels_deleted >= 1 and not DVP in deleter.roles and not AI in deleter.roles:
            if any(role.id == config.ROLES["server_booster"] for role in deleter.roles):
                    roles_to_add = [quarantine, server_booster]
            else:
                    roles_to_add = [quarantine]
            await deleter.edit(roles=roles_to_add, reason="User moved to quarantine for exceeding channel deletion limit.")
            try:
                await log_channel.send(embed=embed)
            except AttributeError:
                pass
        else:
            try:
                await log_channel.send(embed=embed2)
            except AttributeError:
                pass
    if isinstance(channel, disnake.TextChannel) and not DVP in deleter.roles and not AI in deleter.roles:
        new_channel = await guild.create_text_channel(
            name=channel.name,
            position=channel.position,
            category=channel.category,
            overwrites=channel.overwrites,
            reason="Channel recreated after deletion"
        )
        embed4 = disnake.Embed(
            title="Channel Restoration",
            description=f"Restoring `{new_channel}` after deletion...",
            color=disnake.Color.red()
        )
        embed4.set_thumbnail(url = deleter.avatar)
        try:
            await log_channel.send(embed=embed4)
        except AttributeError:
            pass
    elif isinstance(channel, disnake.VoiceChannel) and not DVP in deleter.roles and not AI in deleter.roles:
        new_channel = await guild.create_voice_channel(
            name=channel.name,
            position=channel.position,
            category=channel.category,
            overwrites=channel.overwrites,
            user_limit=channel.user_limit,
            reason="Channel recreated after deletion"
        )
        embed4 = disnake.Embed(
            title="Channel Restoration",
            description=f"Restoring `{new_channel}` after deletion...",
            color=disnake.Color.red()
        )
        embed4.set_thumbnail(url = deleter.avatar)
        await log_channel.send(embed=embed4)

# ================================================================================================ #

@client.event
async def on_message(message):
    log_channel = client.get_channel(config.LOG_CHANNELS["links_spam"])
    log_channel2 = client.get_channel(config.LOG_CHANNELS["webhooks"])
    quarantine = disnake.utils.get(message.guild.roles, id=config.ROLES["quarantine"])
    DVP = disnake.utils.get(message.guild.roles, id=config.ROLES["dvp"])
    server_booster = disnake.utils.get(message.guild.roles, id=config.ROLES["server_booster"])
    if message.webhook_id and ('@everyone' in message.content or '@here' in message.content):
        webhooks = await message.channel.webhooks()
        webhook = None
        for w in webhooks:
            if w.id == message.webhook_id:
                webhook = w
                break
        await message.delete()
        if webhook:
            webhooks = await message.channel.webhooks()
            for webhook in webhooks:
                if webhook.id == message.webhook_id:
                    await webhook.delete()
            await log_channel2.send(embed=disnake.Embed(
                title = f"Webhook Spam",
                description = f"`{webhook.name}` was deleted.",
                color=disnake.Color.red()
            ))        
            
    await client.process_commands(message)

    embed2 = disnake.Embed(
            title="Punishment Issued",
            description=f"{message.author.mention} posted an unauthorized link and was sent to quarantine.",
            color=disnake.Color.red()
        )
    embed2.set_thumbnail(url = message.author.avatar)
    
    if "@here" in message.content or "@everyone" in message.content:
        member = message.guild.get_member(message.author.id)
        if member is not None and (quarantine in member.roles or DVP in member.roles):
            return
        else:
            try:
                await message.delete()
            except disnake.errors.NotFound:
                pass
            await log_channel.send(embed=embed2)
            
            if any(role.id == config.ROLES["server_booster"] for role in member.roles):
                roles_to_add = [quarantine, server_booster]
            else:
                roles_to_add = [quarantine]
            await message.author.edit(roles=roles_to_add, reason="link")
    else:
        await client.process_commands(message)

# ================================================================================================ #

@client.event
async def on_webhooks_update(channel):
    webhooks = await channel.webhooks()
    log_channel = client.get_channel(config.LOG_CHANNELS["webhooks"])
    server_booster = channel.guild.get_role(config.ROLES["server_booster"])
    for webhook in webhooks:
        if webhook.user:
            member = channel.guild.get_member(webhook.user.id)
            if member and not any(role.id == config.ROLES["dvp"] for role in member.roles):
                target_role = channel.guild.get_role(config.ROLES["quarantine"])
                embed = disnake.Embed(
                    title="Punishment Issued",
                    description=f"{member.mention} created a webhook in {channel.mention} and was quarantined\n`Webhook deleted`",
                    color=disnake.Color.red()
                )
                embed.set_thumbnail(url = member.avatar)
                if any(role.id == config.ROLES["server_booster"] for role in member.roles):
                    roles_to_add = [target_role, server_booster]
                else:
                    roles_to_add = [target_role]
                await member.edit(roles=roles_to_add, reason="User moved to quarantine.")
                await log_channel.send(embed=embed)
                try:
                    await webhook.delete()
                except disnake.errors.NotFound:
                    pass
            else:
                embed = disnake.Embed(title="Webhook Creation",description=f"{member.mention} created a webhook in {channel.mention}`",color=disnake.Color.blue())
                await log_channel.send(embed=embed)
                return
                
        if webhook.user.bot:
            await channel.guild.ban(webhook.user, reason="Webhook created by a bot")
            try:
                await webhook.delete()
            except disnake.errors.NotFound:
                pass
        else:
            try:
                await webhook.delete()
            except disnake.errors.NotFound:
                pass

# ================================================================================================ #

@client.event
async def on_member_join(member):
    channel_id = config.LOG_CHANNELS["bot_joins"]
    server_booster = disnake.utils.get(member.guild.roles, id=config.ROLES["server_booster"])
    quarantine = disnake.utils.get(member.guild.roles, id=config.ROLES["quarantine"])
    DVP = disnake.utils.get(member.guild.roles, id=config.ROLES["dvp"])
    if member.bot:
        added_by = None
        async for entry in member.guild.audit_logs(limit=1, action=disnake.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                added_by = entry.user
                break
        if added_by and added_by.id == config.OWNER_ID:
            await client.get_channel(channel_id).send(f"Authorized developer <@config.OWNER_ID> added bot - {member.mention}. All hail the dev!")
        else:
            nickname = added_by
            embed = disnake.Embed(
                title="Bot Joined",
                description=f"Bot {member.mention} added by - {nickname.mention}.\nBot banned, user quarantined.",
                color=disnake.Color.red()
            )
            if any(role.id == config.ROLES["server_booster"] for role in nickname.roles):
                roles_to_add = [quarantine, server_booster]
            else:
                roles_to_add = [quarantine]
            await member.ban(reason='Unauthorized Bot')
            await nickname.edit(roles=roles_to_add, reason = "Adding bot to server")
            await client.get_channel(channel_id).send(embed=embed)
            await client.get_channel(channel_id).send(f"{DVP.mention} - Please investigate")

# ================================================================================================ #

@client.event
async def on_message_edit(before, after):
    if before.content != after.content:
        log_channel = client.get_channel(config.LOG_CHANNELS["message_edit_delete"])
        embed = disnake.Embed(
            title="Message Edited",
            description=f"{before.author.mention} edited their message:",
            color=disnake.Color.blue()
        )
        embed.add_field(name="Original Message", value=f"```{before.content}```", inline=False)
        embed.add_field(name="Edited Message", value=f"```{after.content}```", inline=False)
        embed.add_field(name="Channel", value=f"{before.channel.mention}", inline=False)
        await log_channel.send(embed=embed)

# ================================================================================================ #

@client.event
async def on_message_delete(message):
    log_channel = client.get_channel(config.LOG_CHANNELS["message_edit_delete"])
    author = message.author
    content = message.content
    channel = message.channel
    deleter = message.guild.me.mention
    embed = disnake.Embed(
        title="Message Deleted",
        description=f"{author.mention} Deleted message {deleter}: ",
        color=disnake.Color.red()
    )
    embed.add_field(name="Message", value=f"```{content}```", inline=False)
    embed.add_field(name="Channel", value=f"{channel.mention}", inline=False)
    await log_channel.send(embed=embed)

# ================================================================================================ #

@client.event
async def on_voice_state_update(member, before, after):
    if member.id in user_ids and before.channel != after.channel and after.channel is not None:
        channel = client.get_channel(config.LOG_CHANNELS["voice_move"])
        await member.move_to(channel)

# ================================================================================================ #

@client.event
async def on_member_update(before, after):
    channel_id = config.LOG_CHANNELS["role_updates"]
    DVP = after.guild.get_role(config.ROLES["dvp"])
    AI = after.guild.get_role(config.ROLES["ai"])
    quarantine = after.guild.get_role(config.ROLES["quarantine"])
    server_booster = after.guild.get_role(config.ROLES["server_booster"])
    added_roles = set(after.roles) - set(before.roles)
    removed_roles = set(before.roles) - set(after.roles)

    for role in added_roles:
        role_mentions = role.mention
        async for entry in after.guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == after.id and entry.user.id != client.user.id:
                before_roles = set(entry.changes.before.roles)
                after_roles = set(entry.changes.after.roles)
                if role in after_roles - before_roles:
                    user = entry.user

                    if role.permissions.administrator and not DVP in user.roles:
                        embed = disnake.Embed(
                            title=f"Role Assignment",
                            description=f"{user.mention} gave admin permissions - {role.mention} to user - {after.mention}\n and was sent to {quarantine.mention}",
                            color=disnake.Color.red()
                        )
                        embed.set_thumbnail(url = user.avatar)
                        if any(role.id == config.ROLES["server_booster"] for role in user.roles):
                            roles_to_add = [quarantine, server_booster]
                        else:
                            roles_to_add = [quarantine]
                        await user.edit(roles=roles_to_add)
                        await after.remove_roles(role)
                    else:
                        embed = disnake.Embed(
                            title=f"Role Assignment",
                            color=disnake.Color.green()
                        )
                        embed.add_field(name="Action", value=f"{user.mention} assigned to {after.mention}", inline=False)
                        embed.add_field(name="Role", value=f"{role_mentions}", inline=False)
                        embed.set_thumbnail(url = user.avatar)
                    await client.get_channel(channel_id).send(embed=embed)
                    break
    
    for role in removed_roles:
        role_mentions = role.mention
        async for entry in after.guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
            if entry.target.id == after.id and entry.user.id != client.user.id:
                before_roles = set(entry.changes.before.roles)
                after_roles = set(entry.changes.after.roles)
                if role in before_roles - after_roles:
                    user = entry.user

                    if role.name == "Ai" and not DVP in user.roles:
                        if any(role.id == config.ROLES["server_booster"] for role in user.roles):
                            roles_to_add = [quarantine, server_booster]
                        else:
                            roles_to_add = [quarantine]
                        await user.edit(roles=roles_to_add)
                        await after.add_roles(AI)
                        embed = disnake.Embed(
                            title=f"Role Removal",
                            description=f"{user.mention} removed AI role {role.name}, from bot {after.mention} and got {quarantine.mention}.",
                            color=disnake.Color.red()
                        )
                        embed.set_thumbnail(url = user.avatar)
                    else:
                        embed = disnake.Embed(
                            title=f"Role Removal",
                            color=disnake.Color.blue()
                        )
                        embed.add_field(name="Action", value=f"{user.mention} removed role from {after.mention}", inline=False)
                        embed.add_field(name="Role", value=f"{role.mention}", inline=False)
                        embed.set_thumbnail(url = user.avatar)
                    await client.get_channel(channel_id).send(embed=embed)
                    break

async def remove_all_roles(member):
    for role in member.roles:
        if role != member.guild.default_role:
            await member.remove_roles(role)

# ================================================================================================ #

@client.event
async def on_guild_role_update(before, after):
    channel_id = config.LOG_CHANNELS["role_updates"]
    
    if before.permissions != after.permissions:
        if after.permissions.administrator:
            audit_log = await after.guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_update).flatten()
            member = audit_log[0].user
            if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
                await revert_role_settings(after, before.guild)
            else:
                embed = disnake.Embed(
                    title=f"Role Permissions Changed",
                    description=f"{member.mention} gave admin permissions to role",
                    color=disnake.Color.blue())
                embed.set_thumbnail(url = member.avatar)
                await client.get_channel(channel_id).send(embed=embed)
                
async def revert_role_settings(role, guild):
    channel_id = config.LOG_CHANNELS["role_updates"]
    quarantine = guild.get_role(config.ROLES["quarantine"])
    server_booster = guild.get_role(config.ROLES["server_booster"])
    default_role = guild.default_role  
    audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_update).flatten()
    member = audit_log[0].user
    await role.edit(
        name= role.name,
        permissions=default_role.permissions,
        color=role.color,
        hoist=default_role.hoist,
        mentionable=default_role.mentionable
    )
    embed = disnake.Embed(
        title=f"Role Permissions Changed",
        description=f"Role - {role.mention} was given admin permissions.\nBy - {member.mention}\n```User Quarantined```",
        color=disnake.Color.red())
    embed.set_thumbnail(url = member.avatar)
    await role.edit(name=role.name, permissions=default_role.permissions, color=role.color, hoist=default_role.hoist, mentionable=default_role.mentionable)
    await client.get_channel(channel_id).send(embed=embed)
    if any(role.id == config.ROLES["server_booster"] for role in member.roles):
        roles_to_add = [quarantine, server_booster]
    else:
        roles_to_add = [quarantine]
    await member.edit(roles=roles_to_add)

# ================================================================================================ #

@client.event
async def on_guild_role_create(role):
    guild = role.guild
    channel_id = config.LOG_CHANNELS["role_updates"]
    quarantine = guild.get_role(config.ROLES["quarantine"])
    DVP = guild.get_role(config.ROLES["dvp"])
    server_booster = guild.get_role(config.ROLES["server_booster"])
    audit_log = await role.guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_create).flatten()
    member = audit_log[0].user

    if member.bot:
        if disnake.utils.get(member.roles, name="Ai"):
            embed1 = disnake.Embed(
                title=f"Role Created",
                description=f"Bot - {member.mention}, created role `{role.name}`",
                color=disnake.Color.blue())
            embed1.set_thumbnail(url = member.avatar)
        else:
            await role.delete()
            await member.ban(reason="Role Created without AI")
            embed1 = disnake.Embed(
                title=f"Role Created",
                description=f"Bot - {member.mention}, created role `{role.name}`. and was banned",
                color=disnake.Color.dark_red())
            embed1.set_thumbnail(url = member.avatar)
        await client.get_channel(channel_id).send(embed=embed1)
    
    else:
        if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
            await role.delete()
            if any(role.id == config.ROLES["server_booster"] for role in member.roles):
                roles_to_add = [quarantine, server_booster]
            else:
                roles_to_add = [quarantine]
            await member.edit(roles=roles_to_add)
            embed = disnake.Embed(
                title=f"Role Created",
                description=f"User - {member.mention}, created role `{role.name}`. and was quarantined",
                color=disnake.Color.red())
            embed.set_thumbnail(url = member.avatar)
        else:
            embed = disnake.Embed(
                title=f"Role Created",
                description=f"User - {member.mention}, created role - {role.mention}",
                color=disnake.Color.green())
            embed.set_thumbnail(url = member.avatar)
        await client.get_channel(channel_id).send(embed=embed)

# ================================================================================================ #

@client.event
async def on_guild_role_delete(role):
    guild = role.guild
    channel_id = config.LOG_CHANNELS["role_updates"]
    quarantine = guild.get_role(config.ROLES["quarantine"])
    server_booster = guild.get_role(config.ROLES["server_booster"])
    audit_log = await role.guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_delete).flatten()
    member = audit_log[0].user
    if role.managed: 
        return

    if member.bot:
        if disnake.utils.get(member.roles, name="Ai"):
            embed1 = disnake.Embed(
                title=f"Role Deleted",
                description=f"Bot - {member.mention}, deleted role `{role.name}`.",
                color=disnake.Color.blue())
            embed1.set_thumbnail(url = member.avatar)
        else:
            await role.delete()
            await member.ban(reason="Role Deleted without AI")
            embed1 = disnake.Embed(
                title=f"Role Created",
                description=f"Bot - {member.mention}, deleted role `{role.name}`. and was banned",
                color=disnake.Color.dark_red())
            embed1.set_thumbnail(url = member.avatar)
        await client.get_channel(channel_id).send(embed=embed1)
        
    else:
        if disnake.utils.get(member.roles, id=config.ROLES["dvp"]) is None:
            new_role = await role.guild.create_role(
                name=role.name,
                color=role.color,
                hoist=role.hoist,
                mentionable=role.mentionable,
                reason=f'Recreated role "{role.name}" after deletion by {member.name}'
            )
            embed = disnake.Embed(
                title=f"Role Deleted",
                description=f"User - {member.mention}, deleted role - `{role.name}`.\n***and was quarantined.***\nRole restored - {new_role.mention}```Please move it to its original position```",
                color=disnake.Color.red())
            embed.set_thumbnail(url = member.avatar)
            if any(role.id == config.ROLES["server_booster"] for role in member.roles):
                roles_to_add = [quarantine, server_booster]
            else:
                roles_to_add = [quarantine]
            await member.edit(roles=roles_to_add)
        else:
            embed = disnake.Embed(
                title=f"Role Deleted",
                description=f"User - {member.mention}, deleted role - `{role.name}`",
                color=disnake.Color.green())
            embed.set_thumbnail(url = member.avatar)
        await client.get_channel(channel_id).send(embed=embed)

# ================================================================================================ #

@client.event
async def on_member_ban(guild, user):
    quarantine = guild.get_role(config.ROLES["quarantine"])
    server_booster = guild.get_role(config.ROLES["server_booster"])
    channel_id = config.LOG_CHANNELS["bans"]
    DVP = guild.get_role(config.ROLES["dvp"])
    audit_log = await guild.audit_logs(limit=1, action=disnake.AuditLogAction.ban).flatten()
    member = audit_log[0].user
    reason = audit_log[0].reason if audit_log else "No reason provided."
    if reason == None:
        reason = 'Reason not provided'
    if not DVP in member.roles:
        embed = disnake.Embed(
            title=f"Ban",
            description=f"",
            color=disnake.Color.red())
        embed.set_thumbnail(url = member.avatar)
        embed.add_field(name="User", value=f"▫{member.mention}", inline=True)
        embed.add_field(name="Banned by", value=f"▫{user.mention}", inline=True)
        embed.add_field(name="Reason", value=f"```{reason},User was unbanned```", inline=False)
        if any(role.id == config.ROLES["server_booster"] for role in member.roles):
            roles_to_add = [quarantine, server_booster]
        else:
            roles_to_add = [quarantine]
        await member.edit(roles=roles_to_add)
        await guild.unban(user, reasFon = "Banned by mistake")
    else:
        embed = disnake.Embed(
            title=f"Ban",
            description=f"",
            color=disnake.Color.dark_red())
        embed.set_thumbnail(url = user.avatar)
        embed.add_field(name="User", value=f"▫{member.mention}", inline=True)
        embed.add_field(name="Banned by", value=f"▫{user.mention}", inline=True)
        embed.add_field(name="Reason", value=f"```{reason}", inline=False)
    await client.get_channel(channel_id).send(embed=embed)    

# ================================================================================================ #

@client.event
async def on_guild_channel_update(before, after):
    channel_id = config.LOG_CHANNELS["channel_create"]
    DVP = after.guild.get_role(config.ROLES["dvp"])
    AI = after.guild.get_role(config.ROLES["ai"])
    quarantine = after.guild.get_role(config.ROLES["quarantine"])
    server_booster = after.guild.get_role(config.ROLES["server_booster"])
    audit_log = await after.guild.audit_logs(limit=1, action=disnake.AuditLogAction.overwrite_update).flatten()
    user = audit_log[0].user
    if user.bot:
        if not AI in user.roles:
            await user.ban(reason="Channel permission changes")
        else:
            embed = disnake.Embed(
                title=f"Channel Updated",
                description=f"",
                color=disnake.Color.blue())
            embed.set_thumbnail(url=user.avatar)
            embed.add_field(name="Bot", value=f"▫{user.mention}", inline=True)
            embed.add_field(name="Channel", value=f"▫{after.mention}", inline=True)
            embed.add_field(name="Action", value=f"```Bot changed channel settings (role manipulation)```", inline=False)
    else:
        if not DVP in user.roles:
            if isinstance(after, disnake.TextChannel):
                if before.overwrites != after.overwrites:
                    for role, overwrite in after.overwrites.items():
                        if isinstance(role, disnake.Role):
                            if overwrite != before.overwrites.get(role):
                                await after.set_permissions(role, overwrite=before.overwrites.get(role))
                                if any(role.id == config.ROLES["server_booster"] for role in user.roles):
                                    roles_to_add = [quarantine, server_booster]
                                else:
                                    roles_to_add = [quarantine]
                                await user.edit(roles=roles_to_add)
                                embed1 = disnake.Embed(
                                    title=f"Channel Updated",
                                    description=f"",
                                    color=disnake.Color.dark_red())
                                embed1.set_thumbnail(url=user.avatar)
                                embed1.add_field(name="User", value=f"▫{user.mention}", inline=True)
                                embed1.add_field(name="Channel", value=f"▫{after.mention}", inline=True)
                                if role is not None:
                                    embed1.add_field(name="Role", value=f"▫{role.mention}", inline=True)
                                embed1.add_field(name="Action", value=f"```Changed role permissions and was quarantined```", inline=False)
                                await client.get_channel(channel_id).send(embed=embed1)

        else:
            for role in after.overwrites:
                if isinstance(role, disnake.Role):
                    if role in before.overwrites:
                        if before.overwrites[role] != after.overwrites[role]:
                            embed = disnake.Embed(
                                title=f"Channel Updated",
                                description=f"",
                                color=disnake.Color.dark_green())
                            embed.set_thumbnail(url=user.avatar)
                            embed.add_field(name="User", value=f"▫{user.mention}", inline=True)
                            embed.add_field(name="Channel", value=f"▫{after.mention}", inline=True)
                            embed.add_field(name="Role", value=f"▫{role.mention}",inline=True)
                            embed.add_field(name="Action", value=f"```Changed channel settings (role manipulation)```", inline=False)
                            await client.get_channel(channel_id).send(embed=embed)

# ================================================================================================ #

@client.command()
async def back(ctx, member: disnake.Member):
    user = member
    channel_id = config.LOG_CHANNELS["role_updates"]
    quarantine = ctx.guild.get_role(config.ROLES["quarantine_alt"])
    if ctx.author.id not in admins:
        embed = disnake.Embed(
            title=f"Roles Restored",description=f"",color=disnake.Color.dark_green())
        embed.set_thumbnail(url=user.avatar)
        embed.add_field(name="Error", value=f"```You don't have permission to use this command```", inline=False)
    else:
        audit_log_entries = await ctx.guild.audit_logs(limit=None, action=disnake.AuditLogAction.member_role_update).flatten()
        roles_removed = []
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        for entry in audit_log_entries:
            if entry.created_at < time_threshold or entry.target.id != user.id:
                continue
            
            roles_before = set(entry.before.roles)
            roles_after = set(entry.after.roles)
            roles_removed += list(roles_before - roles_after)
        
        if roles_removed:
            await user.add_roles(*roles_removed)
            embed = disnake.Embed(
                title=f"Roles Restored",description=f"",color=disnake.Color.dark_green())
            embed.set_thumbnail(url=user.avatar)
            embed.add_field(name="User:", value=f"▫{member.mention}", inline=False)
            embed.add_field(name="Roles:", value=f"{', '.join([role.mention for role in roles_removed])}", inline=False)
            
        else:
            embed = disnake.Embed(
                title=f"Roles Restored",description=f"",color=disnake.Color.dark_green())
            embed.set_thumbnail(url=user.avatar)
            embed.add_field(name="User:", value=f"▫{member.mention}", inline=False)
            embed.add_field(name="Roles:", value=f"User has no removed roles in the last `10` minutes", inline=False)
    await client.get_channel(channel_id).send(embed=embed)

# ================================================================================================ #

@client.command()
async def add_adm(ctx, member: disnake.Member):
    if ctx.author.id != klever:
        await ctx.send(f"{ctx.author.mention}, Only the owner can add/remove administrators: {klever.mention}.")
        return
    
    admins.append(member.id)
    await ctx.send(f"{member.mention} was successfully added to the admin list.")

# ================================================================================================ #

@client.command()
async def remove_adm(ctx, member: disnake.Member):
    if ctx.author.id != klever:
        await ctx.send(f"{ctx.author.mention}, Only the owner can add/remove administrators: {klever.mention}.")
        return
    
    admins.remove(member.id)
    await ctx.send(f"{member.mention} was successfully added to the admin list.",)

# ================================================================================================ #

@client.command()
@commands.check(admins)
async def add_user(ctx, member: disnake.Member = None):
    if ctx.author.id not in admins:
        await ctx.send(f"Not enough admin permissions to use this command")
        return
    if member is None:
        member = ctx.author
    embed = disnake.Embed(title="Added to List",description=f"{member.mention}'s ID has been added to the list.",color=disnake.Color.blue())
    embed2 = disnake.Embed(title="Added to List",description=f"{member.mention}'s ID is already in the list.",color=disnake.Color.blue())
    user_id = member.id
    if user_id == config.OWNER_ID:
        await ctx.send("Access Denied.")
    elif user_id not in user_ids:
        user_ids.append(user_id)
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=embed2)

# ================================================================================================ #

@client.command()
@commands.check(admins)
async def remove_user(ctx, member: disnake.Member = None):
    if ctx.author.id not in admins:
        await ctx.send(f"Not enough admin permissions to use this command")
        return
    if member is None:
        member = ctx.author
    
    user_id = member.id
    embed = disnake.Embed(title="Removed from List",description=f"{member.mention}'s ID has been removed from the list.",color=disnake.Color.blue())
    embed2 = disnake.Embed(title="Removed from List",description=f"{member.mention}'s ID is not in the list..",color=disnake.Color.blue())
    if user_id in user_ids:
        user_ids.remove(user_id)
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=embed2)
                        
client.run('TOKEN')
