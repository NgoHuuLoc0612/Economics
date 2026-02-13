"""
Economics Bot Configuration
Enterprise-grade economic simulation parameters
"""

import os
from typing import Dict, List
from enum import Enum

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "economics_bot"

# Bot Configuration
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DEFAULT_PREFIX = "!"
DEFAULT_CURRENCY = "💰"

# Economic Classes
class EconomicClass(Enum):
    LOWER = "Lower Class"
    MIDDLE = "Middle Class"
    UPPER = "Upper Class"
    ELITE = "Elite"
    OLIGARCH = "Oligarch"

CLASS_THRESHOLDS = {
    EconomicClass.LOWER: (0, 10000),
    EconomicClass.MIDDLE: (10001, 50000),
    EconomicClass.UPPER: (50001, 200000),
    EconomicClass.ELITE: (200001, 1000000),
    EconomicClass.OLIGARCH: (1000001, float('inf'))
}

CLASS_TAX_RATES = {
    EconomicClass.LOWER: 0.05,
    EconomicClass.MIDDLE: 0.15,
    EconomicClass.UPPER: 0.28,
    EconomicClass.ELITE: 0.37,
    EconomicClass.OLIGARCH: 0.45
}

CLASS_BENEFITS = {
    EconomicClass.LOWER: {
        "welfare_eligible": True,
        "loan_interest": 0.12,
        "max_loan": 5000,
        "political_power": 1
    },
    EconomicClass.MIDDLE: {
        "welfare_eligible": False,
        "loan_interest": 0.08,
        "max_loan": 25000,
        "political_power": 3
    },
    EconomicClass.UPPER: {
        "welfare_eligible": False,
        "loan_interest": 0.05,
        "max_loan": 100000,
        "political_power": 7
    },
    EconomicClass.ELITE: {
        "welfare_eligible": False,
        "loan_interest": 0.03,
        "max_loan": 500000,
        "political_power": 15
    },
    EconomicClass.OLIGARCH: {
        "welfare_eligible": False,
        "loan_interest": 0.02,
        "max_loan": 2000000,
        "political_power": 30
    }
}

# Labor Market
JOBS = {
    "unemployed": {
        "base_salary": 0,
        "skill_required": 0,
        "demand_elasticity": 0,
        "automation_risk": 0
    },
    "beggar": {
        "base_salary": 200,
        "skill_required": 0,
        "demand_elasticity": 0.1,
        "automation_risk": 0.05
    },
    "street_cleaner": {
        "base_salary": 500,
        "skill_required": 0,
        "demand_elasticity": 0.2,
        "automation_risk": 0.6
    },
    "dishwasher": {
        "base_salary": 600,
        "skill_required": 0,
        "demand_elasticity": 0.3,
        "automation_risk": 0.7
    },
    "laborer": {
        "base_salary": 800,
        "skill_required": 0,
        "demand_elasticity": 0.2,
        "automation_risk": 0.7
    },
    "garbage_collector": {
        "base_salary": 900,
        "skill_required": 0,
        "demand_elasticity": 0.2,
        "automation_risk": 0.5
    },
    "janitor": {
        "base_salary": 1200,
        "skill_required": 1,
        "demand_elasticity": 0.3,
        "automation_risk": 0.6
    },
    "delivery_driver": {
        "base_salary": 1400,
        "skill_required": 1,
        "demand_elasticity": 0.5,
        "automation_risk": 0.8
    },
    "security_guard": {
        "base_salary": 1500,
        "skill_required": 1,
        "demand_elasticity": 0.3,
        "automation_risk": 0.4
    },
    "cashier": {
        "base_salary": 1600,
        "skill_required": 1,
        "demand_elasticity": 0.4,
        "automation_risk": 0.7
    },
    "waiter": {
        "base_salary": 1700,
        "skill_required": 2,
        "demand_elasticity": 0.5,
        "automation_risk": 0.5
    },
    "warehouse_worker": {
        "base_salary": 2000,
        "skill_required": 2,
        "demand_elasticity": 0.5,
        "automation_risk": 0.5
    },
    "factory_worker": {
        "base_salary": 2200,
        "skill_required": 2,
        "demand_elasticity": 0.4,
        "automation_risk": 0.8
    },
    "receptionist": {
        "base_salary": 2400,
        "skill_required": 2,
        "demand_elasticity": 0.4,
        "automation_risk": 0.6
    },
    "sales_associate": {
        "base_salary": 2600,
        "skill_required": 3,
        "demand_elasticity": 0.6,
        "automation_risk": 0.5
    },
    "barista": {
        "base_salary": 2300,
        "skill_required": 2,
        "demand_elasticity": 0.5,
        "automation_risk": 0.6
    },
    "cook": {
        "base_salary": 2800,
        "skill_required": 3,
        "demand_elasticity": 0.4,
        "automation_risk": 0.4
    },
    "mechanic": {
        "base_salary": 3200,
        "skill_required": 4,
        "demand_elasticity": 0.5,
        "automation_risk": 0.3
    },
    "electrician": {
        "base_salary": 3400,
        "skill_required": 4,
        "demand_elasticity": 0.5,
        "automation_risk": 0.3
    },
    "plumber": {
        "base_salary": 3300,
        "skill_required": 4,
        "demand_elasticity": 0.5,
        "automation_risk": 0.2
    },
    "technician": {
        "base_salary": 3500,
        "skill_required": 4,
        "demand_elasticity": 0.6,
        "automation_risk": 0.3
    },
    "paramedic": {
        "base_salary": 3600,
        "skill_required": 5,
        "demand_elasticity": 0.3,
        "automation_risk": 0.2
    },
    "teacher": {
        "base_salary": 3800,
        "skill_required": 5,
        "demand_elasticity": 0.3,
        "automation_risk": 0.2
    },
    "police_officer": {
        "base_salary": 4000,
        "skill_required": 5,
        "demand_elasticity": 0.3,
        "automation_risk": 0.2
    },
    "firefighter": {
        "base_salary": 4100,
        "skill_required": 5,
        "demand_elasticity": 0.3,
        "automation_risk": 0.1
    },
    "nurse": {
        "base_salary": 4200,
        "skill_required": 5,
        "demand_elasticity": 0.4,
        "automation_risk": 0.2
    },
    "accountant": {
        "base_salary": 4500,
        "skill_required": 6,
        "demand_elasticity": 0.6,
        "automation_risk": 0.5
    },
    "software_developer": {
        "base_salary": 5000,
        "skill_required": 6,
        "demand_elasticity": 0.8,
        "automation_risk": 0.3
    },
    "data_analyst": {
        "base_salary": 4800,
        "skill_required": 6,
        "demand_elasticity": 0.7,
        "automation_risk": 0.4
    },
    "engineer": {
        "base_salary": 5500,
        "skill_required": 7,
        "demand_elasticity": 0.7,
        "automation_risk": 0.4
    },
    "architect": {
        "base_salary": 5600,
        "skill_required": 7,
        "demand_elasticity": 0.6,
        "automation_risk": 0.3
    },
    "manager": {
        "base_salary": 6000,
        "skill_required": 6,
        "demand_elasticity": 0.5,
        "automation_risk": 0.3
    },
    "marketing_manager": {
        "base_salary": 6200,
        "skill_required": 7,
        "demand_elasticity": 0.6,
        "automation_risk": 0.4
    },
    "pharmacist": {
        "base_salary": 6500,
        "skill_required": 8,
        "demand_elasticity": 0.4,
        "automation_risk": 0.3
    },
    "dentist": {
        "base_salary": 7000,
        "skill_required": 8,
        "demand_elasticity": 0.4,
        "automation_risk": 0.2
    },
    "lawyer": {
        "base_salary": 7500,
        "skill_required": 8,
        "demand_elasticity": 0.5,
        "automation_risk": 0.3
    },
    "doctor": {
        "base_salary": 8000,
        "skill_required": 9,
        "demand_elasticity": 0.4,
        "automation_risk": 0.1
    },
    "surgeon": {
        "base_salary": 9000,
        "skill_required": 10,
        "demand_elasticity": 0.3,
        "automation_risk": 0.1
    },
    "pilot": {
        "base_salary": 8500,
        "skill_required": 9,
        "demand_elasticity": 0.5,
        "automation_risk": 0.4
    },
    "investment_banker": {
        "base_salary": 10000,
        "skill_required": 9,
        "demand_elasticity": 0.7,
        "automation_risk": 0.3
    },
    "executive": {
        "base_salary": 12000,
        "skill_required": 9,
        "demand_elasticity": 0.8,
        "automation_risk": 0.2
    },
    "ceo": {
        "base_salary": 15000,
        "skill_required": 10,
        "demand_elasticity": 0.9,
        "automation_risk": 0.1
    },
    "entrepreneur": {
        "base_salary": 18000,
        "skill_required": 8,
        "demand_elasticity": 0.9,
        "automation_risk": 0.1
    }
}

# Economic Cycles
CYCLE_PHASES = ["expansion", "peak", "recession", "trough", "recovery"]
CYCLE_DURATION_DAYS = 28  # 4 weeks per full cycle
PHASE_MODIFIERS = {
    "expansion": {"gdp_growth": 1.15, "unemployment": 0.85, "inflation": 1.10},
    "peak": {"gdp_growth": 1.05, "unemployment": 0.90, "inflation": 1.15},
    "recession": {"gdp_growth": 0.85, "unemployment": 1.30, "inflation": 0.95},
    "trough": {"gdp_growth": 0.80, "unemployment": 1.50, "inflation": 0.90},
    "recovery": {"gdp_growth": 1.10, "unemployment": 1.10, "inflation": 1.02}
}

# Crime System
CRIME_TYPES = {
    "pickpocket": {
        "base_success": 0.4,
        "min_steal": 100,
        "max_steal": 500,
        "jail_time_hours": 2,
        "skill_required": 0
    },
    "robbery": {
        "base_success": 0.25,
        "min_steal": 500,
        "max_steal": 3000,
        "jail_time_hours": 6,
        "skill_required": 3
    },
    "heist": {
        "base_success": 0.15,
        "min_steal": 5000,
        "max_steal": 20000,
        "jail_time_hours": 24,
        "skill_required": 7
    },
    "embezzlement": {
        "base_success": 0.20,
        "min_steal": 10000,
        "max_steal": 50000,
        "jail_time_hours": 48,
        "skill_required": 8
    },
    "tax_evasion": {
        "base_success": 0.35,
        "min_steal": 5000,
        "max_steal": 30000,
        "jail_time_hours": 72,
        "skill_required": 6
    }
}

# Investment Options
INVESTMENT_TYPES = {
    "savings_account": {
        "min_amount": 100,
        "annual_return": 0.02,
        "risk": 0.01,
        "liquidity": 1.0
    },
    "bonds": {
        "min_amount": 1000,
        "annual_return": 0.04,
        "risk": 0.05,
        "liquidity": 0.8
    },
    "stocks": {
        "min_amount": 500,
        "annual_return": 0.08,
        "risk": 0.20,
        "liquidity": 0.9
    },
    "real_estate": {
        "min_amount": 50000,
        "annual_return": 0.06,
        "risk": 0.10,
        "liquidity": 0.3
    },
    "venture_capital": {
        "min_amount": 100000,
        "annual_return": 0.15,
        "risk": 0.40,
        "liquidity": 0.2
    },
    "cryptocurrency": {
        "min_amount": 100,
        "annual_return": 0.20,
        "risk": 0.60,
        "liquidity": 0.95
    }
}

# Political System
POLITICAL_POSITIONS = [
    "mayor",
    "treasurer",
    "police_chief",
    "labor_secretary",
    "central_banker"
]

POLITICAL_POWERS = {
    "mayor": {
        "can_set_tax_rate": True,
        "can_create_laws": True,
        "can_pardon": True,
        "term_days": 14
    },
    "treasurer": {
        "can_distribute_welfare": True,
        "can_adjust_budget": True,
        "term_days": 14
    },
    "police_chief": {
        "can_arrest": True,
        "can_investigate": True,
        "can_set_crime_penalty": True,
        "term_days": 14
    },
    "labor_secretary": {
        "can_set_min_wage": True,
        "can_mediate_strikes": True,
        "term_days": 14
    },
    "central_banker": {
        "can_set_interest_rate": True,
        "can_print_money": True,
        "can_implement_qe": True,
        "term_days": 14
    }
}

# Market Items
BASE_ITEMS = {
    "bread": {"base_price": 5, "elasticity": 0.3, "necessity": 0.9},
    "water": {"base_price": 3, "elasticity": 0.2, "necessity": 1.0},
    "medicine": {"base_price": 50, "elasticity": 0.1, "necessity": 0.8},
    "phone": {"base_price": 500, "elasticity": 0.7, "necessity": 0.4},
    "laptop": {"base_price": 1200, "elasticity": 0.8, "necessity": 0.3},
    "car": {"base_price": 25000, "elasticity": 0.9, "necessity": 0.5},
    "house": {"base_price": 200000, "elasticity": 1.2, "necessity": 0.9},
    "luxury_watch": {"base_price": 5000, "elasticity": 1.5, "necessity": 0.0},
    "yacht": {"base_price": 1000000, "elasticity": 2.0, "necessity": 0.0}
}

# Black Market
BLACK_MARKET_ITEMS = {
    "fake_id": {"price": 500, "illegal_level": 2},
    "stolen_goods": {"price": 1000, "illegal_level": 3},
    "insider_info": {"price": 5000, "illegal_level": 4},
    "laundered_money": {"price": 10000, "illegal_level": 5},
    "political_favor": {"price": 50000, "illegal_level": 6}
}

# Economic Formulas Constants
INFLATION_SENSITIVITY = 0.05
GDP_GROWTH_SENSITIVITY = 0.02
UNEMPLOYMENT_IMPACT = 0.15
GINI_COEFFICIENT_THRESHOLD = 0.45  # Inequality trigger
STRIKE_PROBABILITY_BASE = 0.05
UNION_STRENGTH_MULTIPLIER = 1.5

# Random Events
ECONOMIC_EVENTS = {
    "stock_market_crash": {
        "probability": 0.02,
        "gdp_impact": -0.15,
        "unemployment_impact": 0.25,
        "duration_days": 7
    },
    "tech_boom": {
        "probability": 0.03,
        "gdp_impact": 0.20,
        "unemployment_impact": -0.10,
        "duration_days": 14
    },
    "natural_disaster": {
        "probability": 0.01,
        "gdp_impact": -0.10,
        "unemployment_impact": 0.15,
        "duration_days": 5
    },
    "trade_war": {
        "probability": 0.02,
        "gdp_impact": -0.08,
        "unemployment_impact": 0.12,
        "duration_days": 21
    },
    "innovation_breakthrough": {
        "probability": 0.02,
        "gdp_impact": 0.15,
        "unemployment_impact": -0.05,
        "duration_days": 30
    },
    "pandemic": {
        "probability": 0.005,
        "gdp_impact": -0.25,
        "unemployment_impact": 0.40,
        "duration_days": 60
    },
    "oil_crisis": {
        "probability": 0.015,
        "gdp_impact": -0.12,
        "unemployment_impact": 0.08,
        "duration_days": 14
    },
    "housing_bubble": {
        "probability": 0.01,
        "gdp_impact": -0.20,
        "unemployment_impact": 0.30,
        "duration_days": 10
    }
}

# Welfare System
WELFARE_THRESHOLD = 5000
WELFARE_PAYMENT = 500
UNEMPLOYMENT_BENEFIT_RATE = 0.4  # 40% of last salary

# Guild/Corporation System
CORPORATION_COSTS = {
    "startup": 10000,
    "small_business": 50000,
    "corporation": 200000,
    "conglomerate": 1000000
}

CORPORATION_BENEFITS = {
    "startup": {"employees": 5, "tax_rate": 0.10, "influence": 1},
    "small_business": {"employees": 20, "tax_rate": 0.15, "influence": 3},
    "corporation": {"employees": 100, "tax_rate": 0.21, "influence": 10},
    "conglomerate": {"employees": 500, "tax_rate": 0.25, "influence": 25}
}

# API Keys (External Data)
COINGECKO_API = "https://api.coingecko.com/api/v3"
GOLD_API = "https://api.metalpriceapi.com/v1/latest?api_key=demo&base=USD&currencies=XAU"
GOLD_API_BACKUP = "https://www.goldapi.io/api/XAU/USD"
FOREX_API = "https://api.exchangerate-api.com/v4/latest/USD"

# Cooldowns (in seconds)
COOLDOWNS = {
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
    "work": 28800,  # 8 hours
    "crime": 21600,  # 6 hours
    "rob": 43200,  # 12 hours
    "vote": 86400
}

# Achievement System
ACHIEVEMENTS = {
    "first_million": {"reward": 10000, "title": "Millionaire"},
    "first_bankruptcy": {"reward": 1000, "title": "Fallen"},
    "elected_mayor": {"reward": 25000, "title": "Leader"},
    "successful_heist": {"reward": 5000, "title": "Master Thief"},
    "market_manipulator": {"reward": 50000, "title": "Oligarch"},
    "union_organizer": {"reward": 15000, "title": "Labor Hero"},
    "strike_breaker": {"reward": 20000, "title": "Corporate Enforcer"}
}

# Risk and Volatility
MARKET_VOLATILITY_BASE = 0.10
PANIC_THRESHOLD = 0.60  # 60% inequality triggers social unrest
RIOT_PROBABILITY_BASE = 0.01

# Default Server Settings
DEFAULT_SERVER_SETTINGS = {
    "currency_name": "💰 Credits",
    "currency_symbol": "💰",
    "tax_rate": 0.20,
    "inflation_rate": 0.02,
    "interest_rate": 0.05,
    "min_wage": 1500,
    "unemployment_benefit": 600,
    "welfare_amount": 500,
    "lottery_enabled": True,
    "black_market_enabled": True,
    "crime_enabled": True,
    "unions_enabled": True,
    "corporations_enabled": True
}
