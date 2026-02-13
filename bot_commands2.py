"""
Economics Bot Commands (Part 3/3)
Crime, Politics, Market, Server Economy, and Utility Commands
"""

from bot import bot
from discord import app_commands
import discord
from datetime import datetime, timedelta
import random
from config import *
import aiohttp

# ==================== CRIME SYSTEM ====================

@bot.tree.command(name="crime", description="Commit a crime to steal money")
@app_commands.describe(crime_type="Type of crime to commit")
async def crime(interaction: discord.Interaction, crime_type: str):
    """Commit various crimes with risk/reward"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["jail_until"] and datetime.utcnow() < user["jail_until"]:
        remaining = (user["jail_until"] - datetime.utcnow()).total_seconds() / 3600
        await interaction.response.send_message(
            f"🚔 You're in jail for {remaining:.1f} more hours!",
            ephemeral=True
        )
        return
    
    if user.get("last_crime"):
        time_diff = datetime.utcnow() - user["last_crime"]
        if time_diff.total_seconds() < COOLDOWNS["crime"]:
            remaining = (COOLDOWNS["crime"] - time_diff.total_seconds()) / 3600
            await interaction.response.send_message(
                f"⏰ Wait {remaining:.1f} hours before committing another crime",
                ephemeral=True
            )
            return
    
    crime_type = crime_type.lower().replace(" ", "_")
    
    if crime_type not in CRIME_TYPES:
        await interaction.response.send_message("❌ Invalid crime type!", ephemeral=True)
        return
    
    crime_data = CRIME_TYPES[crime_type]
    
    if user["skill_level"] < crime_data["skill_required"]:
        await interaction.response.send_message(
            f"❌ You need skill level {crime_data['skill_required']} to attempt this!",
            ephemeral=True
        )
        return
    
    # Calculate success rate
    success_rate = bot.engine.calculate_crime_success_rate(
        crime_type, user["skill_level"], server["gini_coefficient"],
        0.5, server["unemployment_rate"]
    )
    
    success = random.random() < success_rate
    
    if success:
        stolen_amount = random.uniform(crime_data["min_steal"], crime_data["max_steal"])
        
        await bot.db.update_user(interaction.user.id, interaction.guild.id, {
            "balance": user["balance"] + stolen_amount,
            "reputation": user["reputation"] - 5,
            "last_crime": datetime.utcnow(),
            "statistics.crimes_committed": user["statistics"]["crimes_committed"] + 1,
            "statistics.crimes_success": user["statistics"]["crimes_success"] + 1
        })
        
        await bot.db.record_crime(
            interaction.user.id, interaction.guild.id, crime_type, True, stolen_amount
        )
        
        embed = discord.Embed(
            title="🎉 Crime Successful!",
            description=f"You successfully committed {crime_type.replace('_', ' ')} and got away!",
            color=discord.Color.green()
        )
        embed.add_field(name="Stolen", value=f"{server['settings']['currency_symbol']} {stolen_amount:,.2f}", inline=True)
        embed.add_field(name="Reputation", value=f"-5 (Now: {user['reputation'] - 5})", inline=True)
        
    else:
        fine = random.uniform(crime_data["min_steal"], crime_data["max_steal"]) * 0.5
        fine = min(fine, user["balance"])
        
        jail_time = timedelta(hours=crime_data["jail_time_hours"])
        jail_until = datetime.utcnow() + jail_time
        
        await bot.db.update_user(interaction.user.id, interaction.guild.id, {
            "balance": user["balance"] - fine,
            "jail_until": jail_until,
            "reputation": user["reputation"] - 10,
            "last_crime": datetime.utcnow(),
            "statistics.crimes_committed": user["statistics"]["crimes_committed"] + 1
        })
        
        await bot.db.record_crime(
            interaction.user.id, interaction.guild.id, crime_type, False, fine
        )
        
        embed = discord.Embed(
            title="🚔 Crime Failed!",
            description=f"You got caught attempting {crime_type.replace('_', ' ')}!",
            color=discord.Color.red()
        )
        embed.add_field(name="Fine", value=f"{server['settings']['currency_symbol']} {fine:,.2f}", inline=True)
        embed.add_field(name="Jail Time", value=f"{crime_data['jail_time_hours']} hours", inline=True)
        embed.add_field(name="Reputation", value=f"-10 (Now: {user['reputation'] - 10})", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rob", description="Rob another user")
@app_commands.describe(target="User to rob")
async def rob(interaction: discord.Interaction, target: discord.Member):
    """Rob another user"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    victim = await bot.db.get_user(target.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if target.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't rob yourself!", ephemeral=True)
        return
    
    if target.bot:
        await interaction.response.send_message("❌ You can't rob bots!", ephemeral=True)
        return
    
    if user.get("last_rob"):
        time_diff = datetime.utcnow() - user["last_rob"]
        if time_diff.total_seconds() < COOLDOWNS["rob"]:
            remaining = (COOLDOWNS["rob"] - time_diff.total_seconds()) / 3600
            await interaction.response.send_message(
                f"⏰ Wait {remaining:.1f} hours before robbing again",
                ephemeral=True
            )
            return
    
    if victim["balance"] < 100:
        await interaction.response.send_message(
            "❌ Target doesn't have enough money to rob!",
            ephemeral=True
        )
        return
    
    # Success rate based on skill difference
    skill_diff = user["skill_level"] - victim["skill_level"]
    base_success = 0.4 + (skill_diff * 0.05)
    success_rate = max(0.1, min(base_success, 0.9))
    
    success = random.random() < success_rate
    
    if success:
        steal_amount = victim["balance"] * random.uniform(0.1, 0.3)
        
        await bot.db.update_user(interaction.user.id, interaction.guild.id, {
            "balance": user["balance"] + steal_amount,
            "last_rob": datetime.utcnow(),
            "reputation": user["reputation"] - 3
        })
        
        await bot.db.update_user(target.id, interaction.guild.id, {
            "balance": victim["balance"] - steal_amount
        })
        
        await bot.db.record_transaction(
            interaction.guild.id, target.id, interaction.user.id,
            steal_amount, "robbery"
        )
        
        embed = discord.Embed(
            title="💰 Robbery Successful!",
            description=f"You robbed {target.display_name}!",
            color=discord.Color.green()
        )
        embed.add_field(name="Stolen", value=f"{server['settings']['currency_symbol']} {steal_amount:,.2f}", inline=True)
        
    else:
        fine = user["balance"] * random.uniform(0.1, 0.2)
        
        await bot.db.update_user(interaction.user.id, interaction.guild.id, {
            "balance": user["balance"] - fine,
            "last_rob": datetime.utcnow(),
            "reputation": user["reputation"] - 5
        })
        
        embed = discord.Embed(
            title="🚔 Robbery Failed!",
            description=f"You failed to rob {target.display_name} and got caught!",
            color=discord.Color.red()
        )
        embed.add_field(name="Fine", value=f"{server['settings']['currency_symbol']} {fine:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

# ==================== POLITICAL SYSTEM ====================

@bot.tree.command(name="runforelection", description="Run for a political position")
@app_commands.describe(position="Position to run for (mayor, treasurer, etc.)")
async def runforelection(interaction: discord.Interaction, position: str):
    """Run for political office"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    position = position.lower().replace(" ", "_")
    
    if position not in POLITICAL_POSITIONS:
        await interaction.response.send_message("❌ Invalid position!", ephemeral=True)
        return
    
    # Check if election already active
    active_election = await bot.db.get_active_election(interaction.guild.id, position)
    if active_election:
        await interaction.response.send_message(
            f"❌ An election for {position} is already in progress!",
            ephemeral=True
        )
        return
    
    # Political power requirement
    total_wealth = user["balance"] + user["bank"]
    political_power = bot.engine.calculate_political_influence(
        total_wealth, bot.engine.calculate_economic_class(total_wealth)
    )
    
    min_power_required = {
        "mayor": 10,
        "treasurer": 8,
        "police_chief": 7,
        "labor_secretary": 5,
        "central_banker": 12
    }
    
    if political_power < min_power_required.get(position, 5):
        await interaction.response.send_message(
            f"❌ You need at least {min_power_required[position]} political power! (You have {political_power})",
            ephemeral=True
        )
        return
    
    # Create election
    election = await bot.db.create_election(
        interaction.guild.id, position, [interaction.user.id], duration_hours=48
    )
    
    embed = discord.Embed(
        title=f"🗳️ Election Started!",
        description=f"{interaction.user.display_name} is running for {position.replace('_', ' ').title()}!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Voting Period", value="48 hours", inline=True)
    embed.add_field(name="Your Political Power", value=f"{political_power}", inline=True)
    embed.set_footer(text="Use /vote to cast your vote!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vote", description="Vote in an active election")
@app_commands.describe(position="Position election", candidate="User to vote for")
async def vote(interaction: discord.Interaction, position: str, candidate: discord.Member):
    """Vote in election"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    
    position = position.lower().replace(" ", "_")
    election = await bot.db.get_active_election(interaction.guild.id, position)
    
    if not election:
        await interaction.response.send_message("❌ No active election for this position!", ephemeral=True)
        return
    
    if interaction.user.id in election["voters"]:
        await interaction.response.send_message("❌ You already voted!", ephemeral=True)
        return
    
    if candidate.id not in election["candidates"]:
        await interaction.response.send_message("❌ This person is not a candidate!", ephemeral=True)
        return
    
    # Vote weight based on political power
    total_wealth = user["balance"] + user["bank"]
    vote_weight = bot.engine.calculate_political_influence(
        total_wealth, bot.engine.calculate_economic_class(total_wealth)
    )
    
    await bot.db.elections.update_one(
        {"_id": election["_id"]},
        {
            "$push": {"voters": interaction.user.id},
            "$inc": {f"votes.{candidate.id}": vote_weight}
        }
    )
    
    await interaction.response.send_message(
        f"✅ You voted for {candidate.display_name} with {vote_weight} political power!",
        ephemeral=True
    )

@bot.tree.command(name="electionresults", description="View current election results")
@app_commands.describe(position="Position to check")
async def electionresults(interaction: discord.Interaction, position: str):
    """View election results"""
    position = position.lower().replace(" ", "_")
    election = await bot.db.get_active_election(interaction.guild.id, position)
    
    if not election:
        await interaction.response.send_message("❌ No active election!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"🗳️ Election Results: {position.replace('_', ' ').title()}",
        color=discord.Color.blue()
    )
    
    sorted_candidates = sorted(election["votes"].items(), key=lambda x: x[1], reverse=True)
    
    for user_id, votes in sorted_candidates:
        user = await bot.get_or_fetch_user(int(user_id))
        embed.add_field(
            name=user.display_name,
            value=f"Votes: {votes:,.0f}",
            inline=False
        )
    
    time_remaining = election["end_time"] - datetime.utcnow()
    hours_remaining = int(time_remaining.total_seconds() / 3600)
    
    embed.set_footer(text=f"Voting ends in {hours_remaining} hours")
    
    await interaction.response.send_message(embed=embed)

# ==================== MARKET COMMANDS ====================

@bot.tree.command(name="shop", description="View items available for purchase")
async def shop(interaction: discord.Interaction):
    """View market shop"""
    server = await bot.db.get_server(interaction.guild.id)
    
    embed = discord.Embed(
        title="🏪 Market Shop",
        description="Items available for purchase",
        color=discord.Color.green()
    )
    
    for item, price in server["market_prices"].items():
        necessity = BASE_ITEMS[item]["necessity"]
        necessity_text = "Essential" if necessity > 0.7 else "Luxury" if necessity < 0.3 else "Standard"
        
        embed.add_field(
            name=item.replace("_", " ").title(),
            value=f"💰 {server['settings']['currency_symbol']} {price:,.2f}\n"
                  f"Type: {necessity_text}",
            inline=True
        )
    
    embed.set_footer(text=f"Inflation: {server['inflation_rate']:.2%} | Use /buy <item> to purchase")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy", description="Buy an item from the market")
@app_commands.describe(item="Item to buy", quantity="Quantity to buy")
async def buy(interaction: discord.Interaction, item: str, quantity: int = 1):
    """Purchase item from market"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    item = item.lower().replace(" ", "_")
    
    if item not in server["market_prices"]:
        await interaction.response.send_message("❌ Item not found!", ephemeral=True)
        return
    
    if quantity <= 0:
        await interaction.response.send_message("❌ Quantity must be positive!", ephemeral=True)
        return
    
    price = server["market_prices"][item]
    total_cost = price * quantity
    
    if user["balance"] < total_cost:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    # Update inventory
    current_quantity = user["inventory"].get(item, 0)
    new_inventory = user["inventory"].copy()
    new_inventory[item] = current_quantity + quantity
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] - total_cost,
        "inventory": new_inventory,
        "statistics.total_spent": user["statistics"]["total_spent"] + total_cost
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, interaction.user.id, 0,
        total_cost, "market_purchase", {"item": item, "quantity": quantity}
    )
    
    embed = discord.Embed(
        title="🛒 Purchase Successful!",
        description=f"Bought **{quantity}x {item.replace('_', ' ').title()}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Cost", value=f"{server['settings']['currency_symbol']} {total_cost:,.2f}", inline=True)
    embed.add_field(name="New Balance", value=f"{user['balance'] - total_cost:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventory", description="View your inventory")
async def inventory(interaction: discord.Interaction):
    """View user inventory"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if not user["inventory"]:
        await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎒 Your Inventory",
        color=discord.Color.blue()
    )
    
    total_value = 0
    for item, quantity in user["inventory"].items():
        if quantity > 0:
            current_price = server["market_prices"].get(item, 0)
            item_value = current_price * quantity
            total_value += item_value
            
            embed.add_field(
                name=item.replace("_", " ").title(),
                value=f"Quantity: {quantity}\n"
                      f"Value: {server['settings']['currency_symbol']} {item_value:,.2f}",
                inline=True
            )
    
    embed.description = f"**Total Inventory Value:** {server['settings']['currency_symbol']} {total_value:,.2f}"
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sell", description="Sell items from your inventory")
@app_commands.describe(item="Item to sell", quantity="Quantity to sell")
async def sell(interaction: discord.Interaction, item: str, quantity: int = 1):
    """Sell inventory items"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    item = item.lower().replace(" ", "_")
    
    current_quantity = user["inventory"].get(item, 0)
    
    if current_quantity < quantity:
        await interaction.response.send_message("❌ You don't have enough of this item!", ephemeral=True)
        return
    
    # Sell at 70% of market price
    market_price = server["market_prices"].get(item, 0)
    sell_price = market_price * 0.7
    total_earnings = sell_price * quantity
    
    new_inventory = user["inventory"].copy()
    new_inventory[item] = current_quantity - quantity
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] + total_earnings,
        "inventory": new_inventory,
        "statistics.total_earned": user["statistics"]["total_earned"] + total_earnings
    })
    
    embed = discord.Embed(
        title="💰 Sold Items!",
        description=f"Sold **{quantity}x {item.replace('_', ' ').title()}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Earnings", value=f"{server['settings']['currency_symbol']} {total_earnings:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

# ==================== EXTERNAL DATA COMMANDS ====================

@bot.tree.command(name="gold", description="Check current gold prices")
async def gold(interaction: discord.Interaction):
    """Fetch real gold prices"""
    try:
        async with aiohttp.ClientSession() as session:
            # Using free gold API (no auth needed)
            url = "https://api.gold-api.com/price/XAU"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    gold_price = data.get("price", 0)
                    
                    embed = discord.Embed(
                        title="💎 Gold Price (XAU)",
                        description=f"Current spot price: **${gold_price:,.2f}** per oz",
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    
                    await interaction.response.send_message(embed=embed)
                else:
                    # Fallback to static price with note
                    embed = discord.Embed(
                        title="💎 Gold Price (XAU)",
                        description=f"Approximate price: **$2,050** per oz\n*Real-time data unavailable*",
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    await interaction.response.send_message(embed=embed)
    except Exception as e:
        # Show approximate price instead of error
        embed = discord.Embed(
            title="💎 Gold Price (XAU)",
            description=f"Approximate price: **$2,050** per oz\n*Real-time data unavailable*",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="crypto", description="Check cryptocurrency prices")
@app_commands.describe(coin="Cryptocurrency to check (bitcoin, ethereum, etc.)")
async def crypto(interaction: discord.Interaction, coin: str):
    """Fetch crypto prices from CoinGecko"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{COINGECKO_API}/simple/price?ids={coin.lower()}&vs_currencies=usd&include_24hr_change=true"
            async with session.get(url) as response:
                data = await response.json()
                
                if coin.lower() not in data:
                    await interaction.response.send_message("❌ Cryptocurrency not found!", ephemeral=True)
                    return
                
                coin_data = data[coin.lower()]
                price = coin_data["usd"]
                change_24h = coin_data.get("usd_24h_change", 0)
                
                color = discord.Color.green() if change_24h > 0 else discord.Color.red()
                
                embed = discord.Embed(
                    title=f"₿ {coin.title()} Price",
                    description=f"**${price:,.2f}**",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="24h Change", value=f"{change_24h:+.2f}%", inline=True)
                
                await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error fetching crypto price: {e}", ephemeral=True)

# ==================== SERVER ECONOMY COMMANDS ====================

@bot.tree.command(name="economy", description="View server economic statistics")
async def economy(interaction: discord.Interaction):
    """Display server economy dashboard"""
    server = await bot.db.get_server(interaction.guild.id)
    
    # Calculate class distribution
    class_dist = await bot.db.get_class_distribution(interaction.guild.id)
    
    embed = discord.Embed(
        title="📊 Server Economic Dashboard",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="GDP", value=f"{server['settings']['currency_symbol']} {server['gdp']:,.2f}", inline=True)
    embed.add_field(name="Money Supply", value=f"{server['settings']['currency_symbol']} {server['total_money_supply']:,.2f}", inline=True)
    embed.add_field(name="Inflation Rate", value=f"{server['inflation_rate']:.2%}", inline=True)
    
    embed.add_field(name="Economic Cycle", value=server['cycle_phase'].title(), inline=True)
    embed.add_field(name="Unemployment", value=f"{server['unemployment_rate']:.1%}", inline=True)
    embed.add_field(name="Inequality (Gini)", value=f"{server['gini_coefficient']:.2f}", inline=True)
    
    embed.add_field(name="Interest Rate", value=f"{server['interest_rate']:.2%}", inline=True)
    embed.add_field(name="Min Wage", value=f"{server['settings']['currency_symbol']} {server['min_wage']:,.2f}", inline=True)
    embed.add_field(name="Tax Rate", value=f"{server['settings']['tax_rate']:.1%}", inline=True)
    
    # Class distribution
    class_text = "\n".join([f"{cls}: {count}" for cls, count in class_dist.items()])
    embed.add_field(name="Class Distribution", value=class_text or "No data", inline=False)
    
    # Active events
    if server["active_events"]:
        events_text = "\n".join([e["name"].replace("_", " ").title() for e in server["active_events"][:3]])
        embed.add_field(name="Active Events", value=events_text, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="View server wealth leaderboard")
@app_commands.describe(
    category="Leaderboard category (wealth, income, crimes, etc.)"
)
async def leaderboard(interaction: discord.Interaction, category: str = "wealth"):
    """Display leaderboards"""
    server = await bot.db.get_server(interaction.guild.id)
    
    sort_fields = {
        "wealth": "balance",
        "bank": "bank",
        "reputation": "reputation",
        "skill": "skill_level",
        "crimes": "statistics.crimes_success"
    }
    
    sort_by = sort_fields.get(category.lower(), "balance")
    
    top_users = await bot.db.get_leaderboard(interaction.guild.id, sort_by, limit=10)
    
    embed = discord.Embed(
        title=f"🏆 {category.title()} Leaderboard",
        color=discord.Color.gold()
    )
    
    for i, user_data in enumerate(top_users, 1):
        try:
            user = await bot.get_or_fetch_user(user_data["user_id"])
            
            if category.lower() == "wealth":
                value = user_data["balance"] + user_data["bank"]
                value_text = f"{server['settings']['currency_symbol']} {value:,.2f}"
            elif category.lower() == "crimes":
                value = user_data["statistics"]["crimes_success"]
                value_text = f"{value} successful"
            else:
                value = user_data.get(sort_by, 0)
                value_text = f"{value:,.2f}"
            
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
            
            embed.add_field(
                name=f"{medal} {user.display_name}",
                value=value_text,
                inline=False
            )
        except:
            continue
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welfare", description="Claim welfare benefits if eligible")
async def welfare(interaction: discord.Interaction):
    """Claim welfare for low-income users"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    if not CLASS_BENEFITS[economic_class]["welfare_eligible"]:
        await interaction.response.send_message(
            "❌ You're not eligible for welfare benefits!",
            ephemeral=True
        )
        return
    
    if total_wealth > WELFARE_THRESHOLD:
        await interaction.response.send_message(
            "❌ You have too much wealth for welfare!",
            ephemeral=True
        )
        return
    
    is_unemployed = user["job"] == "unemployed"
    welfare_amount = bot.engine.calculate_welfare_payment(server, economic_class, is_unemployed)
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] + welfare_amount
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        welfare_amount, "welfare_payment"
    )
    
    # Deduct from government budget
    await bot.db.update_server(interaction.guild.id, {
        "government_budget": server["government_budget"] - welfare_amount
    })
    
    embed = discord.Embed(
        title="🤝 Welfare Benefits",
        description=f"You received **{server['settings']['currency_symbol']} {welfare_amount:,.2f}**",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="View your detailed statistics")
async def stats(interaction: discord.Interaction):
    """Display user statistics"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    embed = discord.Embed(
        title=f"📊 {interaction.user.display_name}'s Statistics",
        color=discord.Color.blue()
    )
    
    stats = user["statistics"]
    
    embed.add_field(name="Total Earned", value=f"{server['settings']['currency_symbol']} {stats['total_earned']:,.2f}", inline=True)
    embed.add_field(name="Total Spent", value=f"{server['settings']['currency_symbol']} {stats['total_spent']:,.2f}", inline=True)
    embed.add_field(name="Taxes Paid", value=f"{server['settings']['currency_symbol']} {stats['taxes_paid']:,.2f}", inline=True)
    
    embed.add_field(name="Jobs Worked", value=f"{stats['jobs_worked']}", inline=True)
    embed.add_field(name="Loans Taken", value=f"{stats['loans_taken']}", inline=True)
    embed.add_field(name="Investments Made", value=f"{stats['investments_made']}", inline=True)
    
    if stats["crimes_committed"] > 0:
        success_rate = (stats["crimes_success"] / stats["crimes_committed"]) * 100
        embed.add_field(name="Crimes Committed", value=f"{stats['crimes_committed']}", inline=True)
        embed.add_field(name="Crime Success Rate", value=f"{success_rate:.1f}%", inline=True)
    
    created_days = (datetime.utcnow() - user["created_at"]).days
    embed.set_footer(text=f"Account age: {created_days} days")
    
    await interaction.response.send_message(embed=embed)

# ==================== RUN BOT ====================

if __name__ == "__main__":
    import sys
    sys.path.append('/home/claude')
    
    if not BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        sys.exit(1)
    
    bot.run(BOT_TOKEN)
