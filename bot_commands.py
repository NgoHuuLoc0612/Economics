"""
Economics Bot Commands (Part 2/3)
All slash commands for jobs, market, banking, investments, crime, politics
Import this into bot.py
"""

from bot import bot
from discord import app_commands
import discord
from datetime import datetime, timedelta
import random
from config import *
from bson import ObjectId
import aiohttp

# ==================== JOB COMMANDS ====================

@bot.tree.command(name="joblist", description="View all available jobs and requirements")
async def joblist(interaction: discord.Interaction):
    """Display all jobs with requirements and salaries"""
    server = await bot.db.get_server(interaction.guild.id)
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    
    embed = discord.Embed(
        title="💼 Available Jobs",
        description="Choose a job based on your skill level!",
        color=discord.Color.blue()
    )
    
    for job, data in sorted(JOBS.items(), key=lambda x: x[1]["base_salary"]):
        if job == "unemployed":
            continue
            
        salary = bot.engine.calculate_salary(job, server, data["skill_required"], server["cycle_phase"])
        
        # Get employed count, default to 0 if job not in database yet
        employed_count = server["job_market"].get(job, {"employed": 0})["employed"]
        
        status = "✅ Qualified" if user["skill_level"] >= data["skill_required"] else "❌ Need more skill"
        
        embed.add_field(
            name=f"{job.replace('_', ' ').title()}",
            value=f"💰 {server['settings']['currency_symbol']} {salary:,.0f}/shift\n"
                  f"⭐ Skill Required: {data['skill_required']}\n"
                  f"👥 Currently Employed: {employed_count}\n"
                  f"{status}",
            inline=True
        )
    
    embed.set_footer(text="Use /applyjob <job_name> to apply for a job!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="applyjob", description="Apply for a job")
@app_commands.describe(job="The job you want to apply for")
async def applyjob(interaction: discord.Interaction, job: str):
    """Apply for a job if qualified"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    job = job.lower().replace(" ", "_")
    
    if job not in JOBS or job == "unemployed":
        await interaction.response.send_message("❌ Invalid job!", ephemeral=True)
        return
    
    job_data = JOBS[job]
    
    if user["skill_level"] < job_data["skill_required"]:
        await interaction.response.send_message(
            f"❌ You need skill level {job_data['skill_required']} for this job! (You have {user['skill_level']})",
            ephemeral=True
        )
        return
    
    # Initialize job in job_market if it doesn't exist (for new jobs)
    if job not in server["job_market"]:
        server["job_market"][job] = {"employed": 0, "wage_multiplier": 1.0}
        await bot.db.update_server(interaction.guild.id, {
            f"job_market.{job}": {"employed": 0, "wage_multiplier": 1.0}
        })
    
    if user["job"] != "unemployed":
        old_job = user["job"]
        # Initialize old job if needed
        if old_job not in server["job_market"]:
            server["job_market"][old_job] = {"employed": 1, "wage_multiplier": 1.0}
        
        old_employed = server["job_market"][old_job]["employed"]
        await bot.db.update_server(interaction.guild.id, {
            f"job_market.{old_job}.employed": max(0, old_employed - 1)
        })
    
    new_employed = server["job_market"][job]["employed"] + 1
    await bot.db.update_server(interaction.guild.id, {
        f"job_market.{job}.employed": new_employed
    })
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "job": job,
        "experience": 0
    })
    
    salary = bot.engine.calculate_salary(job, server, user["skill_level"], server["cycle_phase"])
    
    embed = discord.Embed(
        title="🎉 Job Application Approved!",
        description=f"Congratulations! You are now a **{job.replace('_', ' ').title()}**!",
        color=discord.Color.green()
    )
    embed.add_field(name="Starting Salary", value=f"{server['settings']['currency_symbol']} {salary:,.2f}/shift", inline=True)
    embed.add_field(name="Your Skill Level", value=f"⭐ {user['skill_level']}/10", inline=True)
    embed.add_field(name="Workers in this field", value=f"👥 {new_employed}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="resign", description="Quit your current job")
async def resign(interaction: discord.Interaction):
    """Resign from current job"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if user["job"] == "unemployed":
        await interaction.response.send_message("❌ You don't have a job!", ephemeral=True)
        return
    
    old_employed = server["job_market"][user["job"]]["employed"]
    await bot.db.update_server(interaction.guild.id, {
        f"job_market.{user['job']}.employed": max(0, old_employed - 1)
    })
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "job": "unemployed",
        "salary": 0
    })
    
    await interaction.response.send_message(f"✅ You resigned from {user['job'].replace('_', ' ').title()}")

# ==================== BANKING COMMANDS ====================

@bot.tree.command(name="deposit", description="Deposit money into your bank")
@app_commands.describe(amount="Amount to deposit (or 'all' for everything)")
async def deposit(interaction: discord.Interaction, amount: str):
    """Deposit money into bank"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if amount.lower() == "all":
        deposit_amount = user["balance"]
    else:
        try:
            deposit_amount = float(amount)
        except ValueError:
            await interaction.response.send_message("❌ Invalid amount!", ephemeral=True)
            return
    
    if deposit_amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if user["balance"] < deposit_amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    new_balance = user["balance"] - deposit_amount
    new_bank = user["bank"] + deposit_amount
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": new_balance,
        "bank": new_bank
    })
    
    embed = discord.Embed(
        title="🏦 Deposit Successful",
        description=f"Deposited **{server['settings']['currency_symbol']} {deposit_amount:,.2f}**",
        color=discord.Color.green()
    )
    embed.add_field(name="New Cash", value=f"{new_balance:,.2f}", inline=True)
    embed.add_field(name="New Bank", value=f"{new_bank:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="withdraw", description="Withdraw money from your bank")
@app_commands.describe(amount="Amount to withdraw (or 'all' for everything)")
async def withdraw(interaction: discord.Interaction, amount: str):
    """Withdraw money from bank"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if amount.lower() == "all":
        withdraw_amount = user["bank"]
    else:
        try:
            withdraw_amount = float(amount)
        except ValueError:
            await interaction.response.send_message("❌ Invalid amount!", ephemeral=True)
            return
    
    if withdraw_amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if user["bank"] < withdraw_amount:
        await interaction.response.send_message("❌ Insufficient funds in bank!", ephemeral=True)
        return
    
    new_bank = user["bank"] - withdraw_amount
    new_balance = user["balance"] + withdraw_amount
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": new_balance,
        "bank": new_bank
    })
    
    embed = discord.Embed(
        title="🏦 Withdrawal Successful",
        description=f"Withdrew **{server['settings']['currency_symbol']} {withdraw_amount:,.2f}**",
        color=discord.Color.green()
    )
    embed.add_field(name="New Bank", value=f"{new_bank:,.2f}", inline=True)
    embed.add_field(name="New Cash", value=f"{new_balance:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="transfer", description="Transfer money to another user")
@app_commands.describe(user="User to transfer to", amount="Amount to transfer")
async def transfer(interaction: discord.Interaction, user: discord.Member, amount: float):
    """Transfer money between users"""
    sender = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    receiver = await bot.db.get_user(user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if sender["balance"] < amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't transfer to yourself!", ephemeral=True)
        return
    
    # Transaction fee (0.5%)
    fee = amount * 0.005
    net_amount = amount - fee
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": sender["balance"] - amount,
        "statistics.total_spent": sender["statistics"]["total_spent"] + amount
    })
    
    await bot.db.update_user(user.id, interaction.guild.id, {
        "balance": receiver["balance"] + net_amount,
        "statistics.total_earned": receiver["statistics"]["total_earned"] + net_amount
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, interaction.user.id, user.id,
        net_amount, "transfer", {"fee": fee}
    )
    
    embed = discord.Embed(
        title="💸 Transfer Complete",
        description=f"Sent **{server['settings']['currency_symbol']} {net_amount:,.2f}** to {user.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Amount", value=f"{amount:,.2f}", inline=True)
    embed.add_field(name="Fee (0.5%)", value=f"{fee:,.2f}", inline=True)
    embed.add_field(name="Net Sent", value=f"{net_amount:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

# ==================== LOAN SYSTEM ====================

@bot.tree.command(name="loan", description="Take out a loan from the bank")
@app_commands.describe(amount="Amount to borrow")
async def loan(interaction: discord.Interaction, amount: float):
    """Take out a loan"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    total_wealth = user["balance"] + user["bank"]
    economic_class = bot.engine.calculate_economic_class(total_wealth)
    
    max_loan = CLASS_BENEFITS[economic_class]["max_loan"]
    
    if amount > max_loan:
        await interaction.response.send_message(
            f"❌ Your class can only borrow up to {server['settings']['currency_symbol']} {max_loan:,.2f}",
            ephemeral=True
        )
        return
    
    active_loans = await bot.db.get_active_loans(interaction.user.id, interaction.guild.id)
    total_debt = sum(l["remaining"] for l in active_loans)
    
    if total_debt + amount > max_loan * 2:
        await interaction.response.send_message("❌ You have too much debt!", ephemeral=True)
        return
    
    credit_score = max(0, min(1, 1 - (total_debt / (max_loan * 2))))
    interest_rate = bot.engine.calculate_loan_interest(
        economic_class, credit_score, server["interest_rate"]
    )
    
    duration_days = 30
    loan_doc = await bot.db.create_loan(
        interaction.user.id, interaction.guild.id, amount, interest_rate, duration_days
    )
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] + amount,
        "statistics.loans_taken": user["statistics"]["loans_taken"] + 1
    })
    
    await bot.db.record_transaction(
        interaction.guild.id, 0, interaction.user.id,
        amount, "loan_disbursement"
    )
    
    embed = discord.Embed(
        title="💳 Loan Approved!",
        description=f"You received **{server['settings']['currency_symbol']} {amount:,.2f}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Interest Rate", value=f"{interest_rate:.2%}", inline=True)
    embed.add_field(name="Total to Repay", value=f"{loan_doc['remaining']:,.2f}", inline=True)
    embed.add_field(name="Due Date", value=loan_doc['due_date'].strftime("%Y-%m-%d"), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="repay", description="Repay your loans")
@app_commands.describe(amount="Amount to repay (or 'all' for maximum)")
async def repay(interaction: discord.Interaction, amount: str):
    """Repay loans"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    loans = await bot.db.get_active_loans(interaction.user.id, interaction.guild.id)
    
    if not loans:
        await interaction.response.send_message("❌ You have no active loans!", ephemeral=True)
        return
    
    total_debt = sum(l["remaining"] for l in loans)
    
    if amount.lower() == "all":
        repay_amount = min(user["balance"], total_debt)
    else:
        try:
            repay_amount = float(amount)
        except ValueError:
            await interaction.response.send_message("❌ Invalid amount!", ephemeral=True)
            return
    
    if repay_amount > user["balance"]:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    remaining_payment = repay_amount
    
    for loan in sorted(loans, key=lambda x: x["due_date"]):
        if remaining_payment <= 0:
            break
            
        payment = min(remaining_payment, loan["remaining"])
        new_remaining = loan["remaining"] - payment
        
        await bot.db.loans.update_one(
            {"_id": loan["_id"]},
            {"$set": {"remaining": new_remaining}}
        )
        
        remaining_payment -= payment
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] - repay_amount
    })
    
    embed = discord.Embed(
        title="💳 Loan Repayment",
        description=f"Repaid **{server['settings']['currency_symbol']} {repay_amount:,.2f}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Remaining Debt", value=f"{total_debt - repay_amount:,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="myloans", description="View your active loans")
async def myloans(interaction: discord.Interaction):
    """View active loans"""
    loans = await bot.db.get_active_loans(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if not loans:
        await interaction.response.send_message("You have no active loans.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="💳 Your Active Loans",
        color=discord.Color.red()
    )
    
    total_debt = 0
    for i, loan in enumerate(loans, 1):
        total_debt += loan["remaining"]
        days_remaining = (loan["due_date"] - datetime.utcnow()).days
        
        embed.add_field(
            name=f"Loan #{i}",
            value=f"Amount: {server['settings']['currency_symbol']} {loan['remaining']:,.2f}\n"
                  f"Interest: {loan['interest_rate']:.2%}\n"
                  f"Due in: {days_remaining} days",
            inline=True
        )
    
    embed.description = f"**Total Debt:** {server['settings']['currency_symbol']} {total_debt:,.2f}"
    
    await interaction.response.send_message(embed=embed)

# ==================== INVESTMENT SYSTEM ====================

@bot.tree.command(name="invest", description="Invest your money")
@app_commands.describe(
    investment_type="Type of investment",
    amount="Amount to invest"
)
async def invest(interaction: discord.Interaction, investment_type: str, amount: float):
    """Make an investment"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    investment_type = investment_type.lower().replace(" ", "_")
    
    if investment_type not in INVESTMENT_TYPES:
        await interaction.response.send_message("❌ Invalid investment type!", ephemeral=True)
        return
    
    inv_data = INVESTMENT_TYPES[investment_type]
    
    if amount < inv_data["min_amount"]:
        await interaction.response.send_message(
            f"❌ Minimum investment: {server['settings']['currency_symbol']} {inv_data['min_amount']:,.2f}",
            ephemeral=True
        )
        return
    
    if user["balance"] < amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    investment = await bot.db.create_investment(
        interaction.user.id, interaction.guild.id, investment_type, amount
    )
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] - amount,
        "statistics.investments_made": user["statistics"]["investments_made"] + 1
    })
    
    embed = discord.Embed(
        title="📈 Investment Made!",
        description=f"Invested **{server['settings']['currency_symbol']} {amount:,.2f}** in {investment_type.replace('_', ' ').title()}",
        color=discord.Color.green()
    )
    embed.add_field(name="Expected Annual Return", value=f"{inv_data['annual_return']:.1%}", inline=True)
    embed.add_field(name="Risk Level", value=f"{inv_data['risk']:.1%}", inline=True)
    embed.add_field(name="Liquidity", value=f"{inv_data['liquidity']:.1%}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="portfolio", description="View your investment portfolio")
async def portfolio(interaction: discord.Interaction):
    """View investments"""
    investments = await bot.db.get_user_investments(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    if not investments:
        await interaction.response.send_message("You have no investments.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📊 Investment Portfolio",
        color=discord.Color.gold()
    )
    
    total_invested = 0
    total_value = 0
    
    for inv in investments:
        total_invested += inv["principal"]
        total_value += inv["current_value"]
        
        profit = inv["current_value"] - inv["principal"]
        return_pct = (profit / inv["principal"]) * 100 if inv["principal"] > 0 else 0
        
        embed.add_field(
            name=inv["type"].replace("_", " ").title(),
            value=f"Invested: {server['settings']['currency_symbol']} {inv['principal']:,.2f}\n"
                  f"Current: {server['settings']['currency_symbol']} {inv['current_value']:,.2f}\n"
                  f"Return: {return_pct:+.2f}%",
            inline=True
        )
    
    total_profit = total_value - total_invested
    
    embed.description = f"**Total Invested:** {server['settings']['currency_symbol']} {total_invested:,.2f}\n" \
                       f"**Current Value:** {server['settings']['currency_symbol']} {total_value:,.2f}\n" \
                       f"**Profit/Loss:** {server['settings']['currency_symbol']} {total_profit:+,.2f}"
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sellinvestment", description="Sell an investment")
@app_commands.describe(investment_type="Type of investment to sell")
async def sellinvestment(interaction: discord.Interaction, investment_type: str):
    """Liquidate investment"""
    user = await bot.db.get_user(interaction.user.id, interaction.guild.id)
    server = await bot.db.get_server(interaction.guild.id)
    
    investment_type = investment_type.lower().replace(" ", "_")
    
    investment = await bot.db.investments.find_one({
        "user_id": interaction.user.id,
        "guild_id": interaction.guild.id,
        "type": investment_type
    })
    
    if not investment:
        await interaction.response.send_message("❌ You don't have this investment!", ephemeral=True)
        return
    
    # Liquidity penalty
    liquidity = INVESTMENT_TYPES[investment_type]["liquidity"]
    proceeds = investment["current_value"] * liquidity
    
    await bot.db.update_user(interaction.user.id, interaction.guild.id, {
        "balance": user["balance"] + proceeds
    })
    
    await bot.db.investments.delete_one({"_id": investment["_id"]})
    
    profit = proceeds - investment["principal"]
    
    embed = discord.Embed(
        title="💰 Investment Sold!",
        description=f"Sold {investment_type.replace('_', ' ').title()}",
        color=discord.Color.green() if profit > 0 else discord.Color.red()
    )
    embed.add_field(name="Initial Investment", value=f"{investment['principal']:,.2f}", inline=True)
    embed.add_field(name="Proceeds", value=f"{proceeds:,.2f}", inline=True)
    embed.add_field(name="Profit/Loss", value=f"{profit:+,.2f}", inline=True)
    
    await interaction.response.send_message(embed=embed)

# Continue in part 3...
