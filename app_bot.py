import nextcord as discord
import os 
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from discord.ext import commands
from dal import DAL
from model import async_session


load_dotenv()
logging.basicConfig(level=logging.INFO)

client = commands.Bot()
client.affiliatedb = DAL(async_session)

def error_embed(content):
    return discord.Embed(color=0xcf3030, title="Error", description=content)

@client.slash_command(name="create", description="Creates a creator code", default_member_permissions=0, dm_permission=False)
async def create_code(
    ctx: discord.Interaction,
    member: discord.Member = discord.SlashOption(name="member", description="Discord member who the code is creater for")
):
    member_check = await client.affiliatedb.get_account(member.id)
    if member_check: 
        await ctx.send(embed=error_embed(f"This person already has a code!"))
        return
    
    account = await client.affiliatedb.create_account(discord_id=member.id, discord_name=member.name, affiliate_link=str(uuid.uuid4()))
    await ctx.send(f"Token given succesfully. Affialite Link: {account.affiliate_link}")
    await ctx.send(f"```{account.affiliate_link}```")
    
@client.slash_command(name="delete", description="Deletes an existing creator code.", default_member_permissions=0, dm_permission=False)
async def delete_code(
    ctx: discord.Interaction,
    member: discord.Member = discord.SlashOption(name="member", description="Discord member who the code is deleted for")
):
    member_check = await client.affiliatedb.get_account(member.id)
    if not member_check: 
        await ctx.send(embed=error_embed("This person doesn't have a code yet."))
        return
        
    await client.affiliatedb.delete_account(member.id)
    await ctx.send(f"Token deleted succesfully")


@client.slash_command(name="add-record", description="Add balance to a user", default_member_permissions=0, dm_permission=False)
async def addrecord_code(
    ctx: discord.Interaction,
    customer: discord.Member = discord.SlashOption(name="customer", description="Discord customer who is using a code"),
    code: str = discord.SlashOption(name="creatorcode", description="a code made for a creator"),
    amount: int = discord.SlashOption(name="amount", description="the amount the customer is putting on the code"),
    comment: str = discord.SlashOption(name= "comment",description="add a comment",required=False)
):
    code_check = await client.affiliatedb.get_account(affiliate_link=code)
    if not code_check:
        await ctx.send(embed=error_embed("Code is invalid!"))
        return
    
    tokens_given = amount * 0.25
    new_tokens = tokens_given + code_check.tokens
    
    new_record = await client.affiliatedb.create_record(discord_id=code_check.discord_id, buyer_discord_id=customer.id,buyer_discord_name=customer.name,amount=amount,comment=comment)
    await client.affiliatedb.update_account(discord_id=code_check.discord_id, tokens=new_tokens)
    await ctx.send(f"Credit added succesfully (id: {new_record.index})")


@client.slash_command(name="remove-tokens", description="removes balance from a user", default_member_permissions=0, dm_permission=False)
async def remove_credit(
    ctx: discord.Interaction,
    member: discord.Member = discord.SlashOption(name="member", description="user whose tokens are removed"),
    amount: int = discord.SlashOption(name="amount", description="the amount the customer is removig from the code")
    
):
    member_check = await client.affiliatedb.get_account(member.id)
    if not member_check:
        await ctx.send(embed=error_embed("User has no code and therefore no credit"))
        return
    
    new_tokens = member_check.tokens - amount
    if new_tokens < 0:
        await ctx.send(embed=error_embed(f"You can't remove more tokens than they own!\n\nThey currently have {member_check.tokens} tokens"))
        return

    
    await client.affiliatedb.update_account(discord_id=member_check.discord_id, tokens=new_tokens)
    await ctx.send(f"Credit deleted succesfully")

@client.slash_command(name="view-affiliate", description="shows stats about a affiliate", default_member_permissions=0, dm_permission=False)
async def view_affiliate(
    ctx: discord.Interaction,
    member: discord.Member = discord.SlashOption(name="member", description="user whose stats are given.")

):
    member_check = await client.affiliatedb.get_account(member.id, records=True)
    if not member_check:
        await ctx.send(embed=error_embed("No stats found!"))
        return
     
    record_view_content = "No records found." if not member_check.records else ""
    for index, record in enumerate(member_check.records, start=1):
        epoch = int(record.date_added.replace(tzinfo=timezone.utc).timestamp())
        relative_timestamp = f"<t:{epoch}:R>"
        record_view_content += f"{index}. {relative_timestamp} - €{record.amount} - <@{record.buyer_discord_id}> (id: {record.index})\n"
    record_view = f"Transaction History:\n{record_view_content}"

    emoji_dot = client.get_emoji(1279797244962537503)
    emoji_link = client.get_emoji(1279782169237131335)

    content = f"{emoji_dot} This person currently has {member_check.tokens} tokens.\n {emoji_dot} Their code has been used {len(member_check.records)} times.\n{emoji_link} Their affiliate code is: ```{member_check.affiliate_link}```\n\n{record_view}"
    embed = discord.Embed(color=0, title="User stats", description=content)

    await ctx.send(embed=embed)
    
        

@client.slash_command(name="remove-record", description="removes a transaction from a user", default_member_permissions=0, dm_permission=False)
async def remove_transaction(
    ctx: discord.Interaction,
    id: int = discord.SlashOption(name="id", description="the id of the transaction")
    
):

    record_check = await client.affiliatedb.get_record(index=id)
    if not record_check:
        await ctx.send(embed=error_embed("This record doesn't exist!"))
        return
    
    account = record_check.account
    new_tokens = account.tokens - record_check.amount * 0.25

    await client.affiliatedb.update_account(discord_id=account.discord_id, tokens=new_tokens)
    await client.affiliatedb.delete_record(index=id)

    await ctx.send("Record deleted succesfully!")

client.run(os.getenv("DISCORD_TOKEN"))

