"""
Economics Bot - Main Bot File (Part 1/3)
Enterprise-grade Discord economy simulation bot
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Literal
import random
import aiohttp

from database import Database
from economic_engine import EconomicEngine
from config import *

class EconomicsBot(commands.Bot):
    """Main bot class with all economic systems integrated"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(command_prefix=DEFAULT_PREFIX, intents=intents)
        
        self.db = Database(MONGODB_URI, DATABASE_NAME)
        self.engine = EconomicEngine(self.db)
        
    async def setup_hook(self):
        """Initialize database and start background tasks"""
        await self.db.initialize_indexes()
        
        # Start background economic simulation
        self.economic_update_loop.start()
        self.loan_check_loop.start()
        self.investment_update_loop.start()
        self.event_trigger_loop.start()
        
        print(f"Economics Bot initialized successfully")
        
        # Sync commands
        await self.tree.sync()
        
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the economy collapse"
            )
        )
    
    @tasks.loop(hours=1)
    async def economic_update_loop(self):
        """Update server economies every hour"""
        try:
            cursor = self.db.servers.find({})
            async for server in cursor:
                await self.update_server_economy(server["guild_id"])
        except Exception as e:
            print(f"Error in economic update loop: {e}")
    
    @tasks.loop(hours=6)
    async def loan_check_loop(self):
        """Check for overdue loans and apply penalties"""
        try:
            overdue_loans = await self.db.loans.find({
                "due_date": {"$lt": datetime.utcnow()},
                "remaining": {"$gt": 0},
                "defaulted": False
            }).to_list(length=None)
            
            for loan in overdue_loans:
                await self.handle_loan_default(loan)
        except Exception as e:
            print(f"Error in loan check loop: {e}")
    
    @tasks.loop(hours=12)
    async def investment_update_loop(self):
        """Update investment values"""
        try:
            cursor = self.db.investments.find({})
            async for investment in cursor:
                await self.update_investment_value(investment)
        except Exception as e:
            print(f"Error in investment update loop: {e}")
    
    @tasks.loop(hours=24)
    async def event_trigger_loop(self):
        """Trigger random economic events"""
        try:
            cursor = self.db.servers.find({})
            async for server in cursor:
                event = self.engine.trigger_economic_event(server)
                if event:
                    await self.announce_economic_event(server["guild_id"], event)
        except Exception as e:
            print(f"Error in event trigger loop: {e}")
    
    async def update_server_economy(self, guild_id: int):
        """Comprehensive server economy update"""
        server = await self.db.get_server(guild_id)
        
        # Update economic cycle
        cycle_update = self.engine.update_economic_cycle(server)
        
        # Calculate GDP
        new_gdp = await self.db.get_gdp(guild_id, days=7)
        
        # Calculate money supply
        cursor = self.db.users.find({"guild_id": guild_id})
        total_money = 0
        async for user in cursor:
            total_money += user["balance"] + user["bank"]
        
        # Calculate inflation
        inflation = self.engine.calculate_inflation(total_money, new_gdp)
        
        # Update market prices based on inflation
        new_prices = {}
        for item, base_price in server["market_prices"].items():
            new_price = self.engine.calculate_item_price(
                item, BASE_ITEMS[item]["base_price"], inflation
            )
            new_prices[item] = new_price
        
        # Calculate Gini coefficient
        gini = await self.db.calculate_gini_coefficient(guild_id)
        
        # Calculate unemployment
        total_users = await self.db.users.count_documents({"guild_id": guild_id})
        unemployment = await self.db.get_unemployment_rate(guild_id)
        
        # Update server data
        await self.db.update_server(guild_id, {
            "cycle_phase": cycle_update["cycle_phase"],
            "gdp": new_gdp,
            "total_money_supply": total_money,
            "inflation_rate": inflation,
            "market_prices": new_prices,
            "gini_coefficient": gini,
            "unemployment_rate": unemployment,
            "last_update": datetime.utcnow()
        })
        
        # Record market snapshot
        await self.db.record_market_snapshot(guild_id, {
            "gdp": new_gdp,
            "inflation": inflation,
            "unemployment": unemployment,
            "gini": gini,
            "cycle_phase": cycle_update["cycle_phase"]
        })
    
    async def handle_loan_default(self, loan: dict):
        """Handle loan default with penalties"""
        user = await self.db.get_user(loan["user_id"], loan["guild_id"])
        
        # Seize assets
        total_assets = user["balance"] + user["bank"]
        seized = min(total_assets, loan["remaining"])
        
        # Update user balance
        remaining_balance = total_assets - seized
        await self.db.update_user(loan["user_id"], loan["guild_id"], {
            "balance": remaining_balance,
            "bank": 0,
            "reputation": user["reputation"] - 50
        })
        
        # Mark loan as defaulted
        await self.db.loans.update_one(
            {"_id": loan["_id"]},
            {"$set": {"defaulted": True, "remaining": max(0, loan["remaining"] - seized)}}
        )
    
    async def update_investment_value(self, investment: dict):
        """Update investment value based on market conditions"""
        server = await self.db.get_server(investment["guild_id"])
        
        days_held = (datetime.utcnow() - investment["last_update"]).days
        if days_held == 0:
            return
            
        market_conditions = {
            "gdp_growth": PHASE_MODIFIERS[server["cycle_phase"]]["gdp_growth"]
        }
        
        return_rate = self.engine.calculate_investment_return(
            investment["type"], market_conditions, days_held
        )
        
        new_value = investment["current_value"] * (1 + return_rate)
        
        await self.db.investments.update_one(
            {"_id": investment["_id"]},
            {"$set": {
                "current_value": new_value,
                "last_update": datetime.utcnow()
            }}
        )
    
    async def announce_economic_event(self, guild_id: int, event: dict):
        """Announce economic event to the server"""
        try:
            guild = self.get_guild(guild_id)
            if not guild:
                return
                
            # Find announcement channel (or use system channel)
            channel = guild.system_channel or guild.text_channels[0]
            
            embed = discord.Embed(
                title=f"📰 Economic Event: {event['name'].replace('_', ' ').title()}",
                description=f"A major economic event has occurred!",
                color=discord.Color.red() if event['data']['gdp_impact'] < 0 else discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="GDP Impact",
                value=f"{event['data']['gdp_impact']:+.1%}",
                inline=True
            )
            embed.add_field(
                name="Unemployment Impact",
                value=f"{event['data']['unemployment_impact']:+.1%}",
                inline=True
            )
            embed.add_field(
                name="Duration",
                value=f"{event['data']['duration_days']} days",
                inline=True
            )
            
            await channel.send(embed=embed)
            
            # Add event to server active events
            await self.db.update_server(guild_id, {
                "$push": {"active_events": event}
            })
            
        except Exception as e:
            print(f"Error announcing event: {e}")

bot = EconomicsBot()

# ==================== CORE USER COMMANDS ====================

@bot.tree.command(name="balance", description="Check your balance and economic status")
async def balance(interaction: discord.Interaction):
    """Display user's complete financial status"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    loans = await bot.db.get_active_loans(interaction.user.id, interaction.guild.id)
    total_debt = sum(loan["remaining"] for loan in loans)
    
    investments = await bot.db.get_user_investments(interaction.user.id, interaction.guild.id)
    investment_value = sum(inv["current_value"] for inv in investments)
    
    net_worth = total_wealth + investment_value - total_debt
    
    embed = discord.Embed(
        title=f"💰 {interaction.user.display_name}'s Financial Status",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Cash", value=f"{server['settings']['currency_symbol']} {user['balance']:,.2f}", inline=True)
    embed.add_field(name="Bank", value=f"{server['settings']['currency_symbol']} {user['bank']:,.2f}", inline=True)
    embed.add_field(name="Total Wealth", value=f"{server['settings']['currency_symbol']} {total_wealth:,.2f}", inline=True)
    
    embed.add_field(name="Economic Class", value=economic_class.value, inline=True)
    embed.add_field(name="Job", value=user['job'].replace('_', ' ').title(), inline=True)
    embed.add_field(name="Skill Level", value=f"⭐ {user['skill_level']}/10", inline=True)
    
    embed.add_field(name="💼 Investments", value=f"{server['settings']['currency_symbol']} {investment_value:,.2f}", inline=True)
    embed.add_field(name="💳 Debt", value=f"{server['settings']['currency_symbol']} {total_debt:,.2f}", inline=True)
    embed.add_field(name="📊 Net Worth", value=f"{server['settings']['currency_symbol']} {net_worth:,.2f}", inline=True)
    
    embed.add_field(name="Political Power", value=f"🗳️ {user['political_power']}", inline=True)
    embed.add_field(name="Reputation", value=f"⭐ {user['reputation']}", inline=True)
    embed.add_field(name="Union Member", value="✅" if user['union_member'] else "❌", inline=True)
    
    embed.set_footer(text=f"Tax Rate: {CLASS_TAX_RATES[economic_class]:.1%}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Claim your daily income")
async def daily(interaction: discord.Interaction):
    """Daily income with class-based bonuses"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["last_daily"]:
        time_diff = datetime.utcnow() - user["last_daily"]
        if time_diff.total_seconds() < COOLDOWNS["daily"]:
            remaining = COOLDOWNS["daily"] - time_diff.total_seconds()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await interaction.response.send_message(
                f"⏰ You already claimed your daily! Come back in {hours}h {minutes}m",
                ephemeral=True
            )
            return
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    base_daily = 100
    class_multiplier = {
        EconomicClass.LOWER: 1.0,
        EconomicClass.MIDDLE: 1.5,
        EconomicClass.UPPER: 2.0,
        EconomicClass.ELITE: 3.0,
        EconomicClass.OLIGARCH: 5.0
    }
    
    daily_amount = base_daily * class_multiplier[economic_class]
    phase_modifier = PHASE_MODIFIERS[server["cycle_phase"]]["gdp_growth"]
    daily_amount *= phase_modifier
    
    streak_bonus = random.randint(0, 50)
    total_amount = daily_amount + streak_bonus
    
    new_balance = user["balance"] + total_amount
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": new_balance,
        "last_daily": datetime.utcnow(),
        "statistics.total_earned": user["statistics"]["total_earned"] + total_amount
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        total_amount, "daily_income"
    )
    
    embed = discord.Embed(
        title="💰 Daily Income Claimed!",
        description=f"You received **{server['settings']['currency_symbol']} {total_amount:,.2f}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Base", value=f"{daily_amount:.2f}", inline=True)
    embed.add_field(name="Streak Bonus", value=f"+{streak_bonus:.2f}", inline=True)
    embed.add_field(name="New Balance", value=f"{new_balance:,.2f}", inline=True)
    embed.set_footer(text=f"Economic Phase: {server['cycle_phase'].title()}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="weekly", description="Claim your weekly bonus")
async def weekly(interaction: discord.Interaction):
    """Weekly bonus - larger than daily"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["last_weekly"]:
        time_diff = datetime.utcnow() - user["last_weekly"]
        if time_diff.total_seconds() < COOLDOWNS["weekly"]:
            remaining = COOLDOWNS["weekly"] - time_diff.total_seconds()
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            await interaction.response.send_message(
                f"⏰ Weekly bonus available in {days}d {hours}h",
                ephemeral=True
            )
            return
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    weekly_amount = 1000 * (1 + list(EconomicClass).index(economic_class) * 0.5)
    
    new_balance = user["balance"] + weekly_amount
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": new_balance,
        "last_weekly": datetime.utcnow(),
        "statistics.total_earned": user["statistics"]["total_earned"] + weekly_amount
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        weekly_amount, "weekly_income"
    )
    
    embed = discord.Embed(
        title="🎁 Weekly Bonus!",
        description=f"You received **{server['settings']['currency_symbol']} {weekly_amount:,.2f}**",
        color=discord.Color.purple()
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="monthly", description="Claim your monthly bonus")
async def monthly(interaction: discord.Interaction):
    """Monthly bonus - largest periodic reward"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["last_monthly"]:
        time_diff = datetime.utcnow() - user["last_monthly"]
        if time_diff.total_seconds() < COOLDOWNS["monthly"]:
            remaining = COOLDOWNS["monthly"] - time_diff.total_seconds()
            days = int(remaining // 86400)
            await interaction.response.send_message(
                f"⏰ Monthly bonus available in {days} days",
                ephemeral=True
            )
            return
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    monthly_amount = 5000 * (1 + list(EconomicClass).index(economic_class))
    
    new_balance = user["balance"] + monthly_amount
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": new_balance,
        "last_monthly": datetime.utcnow(),
        "statistics.total_earned": user["statistics"]["total_earned"] + monthly_amount
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        monthly_amount, "monthly_income"
    )
    
    embed = discord.Embed(
        title="💎 Monthly Bonus!",
        description=f"You received **{server['settings']['currency_symbol']} {monthly_amount:,.2f}**",
        color=discord.Color.dark_gold()
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work", description="Work at your job to earn salary")
async def work(interaction: discord.Interaction):
    """Work to earn salary based on job and skills"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["job"] == "unemployed":
        await interaction.response.send_message(
            "❌ You need to get a job first! Use `/joblist` to see available jobs.",
            ephemeral=True
        )
        return
    
    if user["last_work"]:
        time_diff = datetime.utcnow() - user["last_work"]
        if time_diff.total_seconds() < COOLDOWNS["work"]:
            remaining = COOLDOWNS["work"] - time_diff.total_seconds()
            hours = int(remaining // 3600)
            await interaction.response.send_message(
                f"⏰ You're tired! Rest for {hours} more hours.",
                ephemeral=True
            )
            return
    
    if user["jail_until"] and datetime.utcnow() < user["jail_until"]:
        await interaction.response.send_message("🚔 You can't work while in jail!", ephemeral=True)
        return
    
    salary = bot.engine.calculate_salary(
        user["job"], server, user["skill_level"], server["cycle_phase"]
    )
    
    productivity = bot.engine.calculate_productivity(
        user["skill_level"], user["statistics"]["jobs_worked"], server["cycle_phase"]
    )
    
    earnings = salary * productivity
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    tax = bot.engine.calculate_tax(earnings, economic_class, server["settings"]["tax_rate"])
    
    net_earnings = earnings - tax
    
    skill_gain = random.randint(1, 3) if random.random() < 0.3 else 0
    new_skill = min(user["skill_level"] + skill_gain, 10)
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] + net_earnings,
        "skill_level": new_skill,
        "experience": user["experience"] + 1,
        "last_work": datetime.utcnow(),
        "statistics.jobs_worked": user["statistics"]["jobs_worked"] + 1,
        "statistics.total_earned": user["statistics"]["total_earned"] + net_earnings,
        "statistics.taxes_paid": user["statistics"]["taxes_paid"] + tax
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        net_earnings, "work_income", {"job": user["job"], "tax": tax}
    )
    
    await bot.db.update_server(interaction.guild.id, {
        "tax_revenue": server["tax_revenue"] + tax,
        "government_budget": server["government_budget"] + tax
    })
    
    embed = discord.Embed(
        title=f"💼 {user['job'].replace('_', ' ').title()} Shift Complete",
        description=f"You worked hard and earned money!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Gross Earnings", value=f"{server['settings']['currency_symbol']} {earnings:,.2f}", inline=True)
    embed.add_field(name="Tax ({:.1%})".format(CLASS_TAX_RATES[economic_class]), value=f"-{server['settings']['currency_symbol']} {tax:,.2f}", inline=True)
    embed.add_field(name="Net Earnings", value=f"{server['settings']['currency_symbol']} {net_earnings:,.2f}", inline=True)
    
    if skill_gain > 0:
        embed.add_field(name="Skill Gained", value=f"+{skill_gain} ⭐ (Now: {new_skill}/10)", inline=False)
    
    embed.set_footer(text=f"Productivity: {productivity:.2f}x | Come back in 8 hours")
    
    await interaction.response.send_message(embed=embed)

# PART 1 ENDS - Continue with bot_commands.py for additional commands
