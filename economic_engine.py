"""
Economic Engine - Core Economic Simulation Logic
Handles all economic calculations, cycles, inflation, and market dynamics
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config import *
import numpy as np

class EconomicEngine:
    """
    Enterprise-grade economic simulation engine
    Implements sophisticated economic models and theories
    """
    
    def __init__(self, database):
        self.db = database
        
    def calculate_economic_class(self, wealth: float) -> EconomicClass:
        """Determine user's economic class based on wealth"""
        for econ_class, (min_wealth, max_wealth) in CLASS_THRESHOLDS.items():
            if min_wealth <= wealth <= max_wealth:
                return econ_class
        return EconomicClass.LOWER
    
    def calculate_tax(self, income: float, economic_class: EconomicClass, 
                     server_tax_modifier: float = 1.0) -> float:
        """Calculate progressive tax based on class and server settings"""
        base_rate = CLASS_TAX_RATES[economic_class]
        effective_rate = base_rate * server_tax_modifier
        return income * effective_rate
    
    def calculate_salary(self, job: str, server_data: Dict, user_skill: int,
                        economic_phase: str) -> float:
        """
        Calculate dynamic salary based on:
        - Base job salary
        - Server GDP
        - Economic cycle phase
        - Supply/demand (how many have this job)
        - User skill level
        - Minimum wage laws
        """
        if job == "unemployed":
            return 0
            
        job_data = JOBS[job]
        base_salary = job_data["base_salary"]
        
        # Economic cycle modifier
        phase_modifier = PHASE_MODIFIERS[economic_phase]["gdp_growth"]
        
        # Supply/demand calculation
        job_market = server_data["job_market"].get(job, {"employed": 1, "wage_multiplier": 1.0})
        employed_count = job_market["employed"]
        demand_elasticity = job_data["demand_elasticity"]
        
        # Simple supply/demand: fewer workers = higher wages
        supply_modifier = 1.0 + (demand_elasticity * (1 / max(employed_count, 1)))
        supply_modifier = min(supply_modifier, 2.0)  # Cap at 2x
        
        # Skill bonus (up to 50% increase) - handle skill_required = 0
        skill_required = max(job_data["skill_required"], 1)  # Avoid division by zero
        skill_modifier = 1.0 + (user_skill / skill_required) * 0.5
        skill_modifier = min(skill_modifier, 1.5)
        
        # GDP influence (richer servers pay more)
        gdp_modifier = 1.0 + (server_data["gdp"] / 1000000) * 0.1
        gdp_modifier = min(gdp_modifier, 2.0)
        
        calculated_salary = (base_salary * phase_modifier * supply_modifier * 
                           skill_modifier * gdp_modifier)
        
        # Enforce minimum wage
        min_wage = server_data["min_wage"]
        return max(calculated_salary, min_wage)
    
    def calculate_inflation(self, money_supply: float, gdp: float, 
                           velocity: float = 1.5) -> float:
        """
        Calculate inflation using Quantity Theory of Money: MV = PY
        M = Money Supply
        V = Velocity (how fast money changes hands)
        P = Price Level (what we're solving for)
        Y = Real GDP
        """
        if gdp <= 0:
            return 0.02  # Default 2%
            
        # Price level change
        price_level = (money_supply * velocity) / gdp
        
        # Convert to inflation rate (percentage change)
        inflation_rate = (price_level - 1.0) * INFLATION_SENSITIVITY
        
        # Bound between -5% (deflation) and 20% (hyperinflation)
        return max(-0.05, min(inflation_rate, 0.20))
    
    def calculate_item_price(self, item: str, base_price: float, 
                            inflation_rate: float, demand_factor: float = 1.0) -> float:
        """
        Calculate dynamic item pricing with:
        - Inflation adjustment
        - Supply/demand
        - Elasticity of demand
        """
        item_data = BASE_ITEMS.get(item, {"elasticity": 0.5, "necessity": 0.5})
        
        # Inflation adjustment
        inflation_adjusted = base_price * (1 + inflation_rate)
        
        # Demand adjustment (elastic goods fluctuate more)
        elasticity = item_data["elasticity"]
        demand_adjustment = 1.0 + ((demand_factor - 1.0) * elasticity)
        
        # Necessity floor (essential items don't drop below certain price)
        necessity = item_data["necessity"]
        price_floor = base_price * necessity * 0.5
        
        final_price = inflation_adjusted * demand_adjustment
        return max(final_price, price_floor)
    
    def update_economic_cycle(self, server_data: Dict) -> Dict:
        """
        Update the economic cycle phase
        Full cycle: expansion → peak → recession → trough → recovery
        Each phase lasts approximately 1 week
        """
        cycle_start = server_data["cycle_start"]
        days_elapsed = (datetime.utcnow() - cycle_start).days
        
        phase_duration = CYCLE_DURATION_DAYS / len(CYCLE_PHASES)
        current_phase_index = int(days_elapsed / phase_duration) % len(CYCLE_PHASES)
        new_phase = CYCLE_PHASES[current_phase_index]
        
        # Random shocks can trigger early recession
        if random.random() < 0.05 and new_phase == "expansion":
            new_phase = "recession"
            
        return {
            "cycle_phase": new_phase,
            "phase_modifiers": PHASE_MODIFIERS[new_phase]
        }
    
    def calculate_unemployment_rate(self, server_data: Dict, 
                                   total_users: int) -> float:
        """Calculate unemployment rate based on economic conditions"""
        phase = server_data["cycle_phase"]
        base_unemployment = 0.05  # 5% natural rate
        
        phase_modifier = PHASE_MODIFIERS[phase]["unemployment"]
        calculated_rate = base_unemployment * phase_modifier
        
        # Automation impact
        automation_effect = sum(
            JOBS[job]["automation_risk"] * server_data["job_market"][job]["employed"]
            for job in JOBS.keys()
        ) / max(total_users, 1)
        
        calculated_rate += automation_effect * 0.1
        
        return min(calculated_rate, 0.50)  # Cap at 50%
    
    def calculate_crime_success_rate(self, crime_type: str, user_skill: int,
                                    inequality: float, police_strength: float,
                                    unemployment_rate: float) -> float:
        """
        Calculate crime success probability based on:
        - Base success rate
        - User skill
        - Inequality (higher inequality = more crime)
        - Police presence
        - Unemployment (desperate people commit more crime)
        """
        crime_data = CRIME_TYPES[crime_type]
        base_success = crime_data["base_success"]
        
        # Skill bonus
        skill_required = crime_data["skill_required"]
        skill_bonus = (user_skill - skill_required) * 0.05
        
        # Inequality bonus (Gini > 0.45 increases crime)
        inequality_bonus = max(0, (inequality - 0.45) * 0.5)
        
        # Unemployment desperation
        unemployment_bonus = unemployment_rate * 0.3
        
        # Police deterrent
        police_penalty = police_strength * 0.2
        
        success_rate = (base_success + skill_bonus + inequality_bonus + 
                       unemployment_bonus - police_penalty)
        
        return max(0.05, min(success_rate, 0.95))
    
    def calculate_strike_probability(self, job: str, server_data: Dict,
                                    union_strength: float) -> float:
        """Calculate probability of workers going on strike"""
        job_market = server_data["job_market"][job]
        wage = self.calculate_salary(job, server_data, 5, server_data["cycle_phase"])
        min_wage = server_data["min_wage"]
        
        # Low wages increase strike probability
        wage_dissatisfaction = max(0, (min_wage * 1.5 - wage) / (min_wage * 1.5))
        
        # Unemployment makes workers less likely to strike (fear of replacement)
        unemployment = server_data["unemployment_rate"]
        unemployment_deterrent = unemployment * 0.5
        
        # Union strength multiplier
        base_probability = STRIKE_PROBABILITY_BASE
        
        strike_prob = (base_probability + wage_dissatisfaction * 0.3 - 
                      unemployment_deterrent) * union_strength
        
        return max(0, min(strike_prob, 0.80))
    
    def calculate_loan_interest(self, economic_class: EconomicClass,
                               credit_score: float, server_interest_rate: float) -> float:
        """
        Calculate loan interest rate based on:
        - Economic class (creditworthiness proxy)
        - Credit score
        - Server's base interest rate (central bank policy)
        """
        class_rate = CLASS_BENEFITS[economic_class]["loan_interest"]
        
        # Credit score adjustment (-50% to +100% of class rate)
        credit_modifier = 1.0 + (0.5 - credit_score)
        
        # Server rate influence
        rate_modifier = 1.0 + (server_interest_rate - 0.05) * 2
        
        final_rate = class_rate * credit_modifier * rate_modifier
        
        return max(0.01, min(final_rate, 0.50))  # Between 1% and 50%
    
    def calculate_investment_return(self, investment_type: str, 
                                   market_conditions: Dict,
                                   holding_period_days: int) -> float:
        """
        Calculate investment returns with realistic volatility
        Uses geometric Brownian motion for stock-like assets
        """
        investment_data = INVESTMENT_TYPES[investment_type]
        annual_return = investment_data["annual_return"]
        risk = investment_data["risk"]
        
        # Annualize based on holding period
        time_factor = holding_period_days / 365.0
        
        # Expected return
        expected_return = annual_return * time_factor
        
        # Market condition adjustment
        gdp_growth = market_conditions.get("gdp_growth", 1.0)
        market_modifier = (gdp_growth - 0.9) * 2  # -20% to +20%
        
        # Volatility (random walk)
        volatility = risk * math.sqrt(time_factor)
        random_shock = random.gauss(0, volatility)
        
        # Total return
        total_return = expected_return + market_modifier + random_shock
        
        # Realistic bounds
        if investment_type == "cryptocurrency":
            return max(-0.90, min(total_return, 5.0))  # -90% to +500%
        elif investment_type == "venture_capital":
            return max(-0.80, min(total_return, 3.0))  # -80% to +300%
        else:
            return max(-0.50, min(total_return, 1.0))  # -50% to +100%
    
    def trigger_economic_event(self, server_data: Dict) -> Optional[Dict]:
        """Randomly trigger economic events (crises, booms, etc.)"""
        for event_name, event_data in ECONOMIC_EVENTS.items():
            if random.random() < event_data["probability"]:
                return {
                    "name": event_name,
                    "data": event_data,
                    "start_time": datetime.utcnow(),
                    "end_time": datetime.utcnow() + timedelta(days=event_data["duration_days"])
                }
        return None
    
    def apply_event_effects(self, server_data: Dict, event: Dict) -> Dict:
        """Apply effects of an active economic event"""
        event_data = event["data"]
        
        # Check if event is still active
        if datetime.utcnow() > event["end_time"]:
            return {"remove_event": True}
        
        # Apply GDP impact
        gdp_modifier = 1.0 + event_data["gdp_impact"]
        unemployment_modifier = 1.0 + event_data["unemployment_impact"]
        
        return {
            "gdp_modifier": gdp_modifier,
            "unemployment_modifier": unemployment_modifier
        }
    
    def calculate_political_influence(self, wealth: float, 
                                     economic_class: EconomicClass,
                                     corporation_influence: int = 0) -> int:
        """Calculate user's political power/influence"""
        base_power = CLASS_BENEFITS[economic_class]["political_power"]
        
        # Wealth influence (logarithmic scale)
        wealth_power = int(math.log10(max(wealth, 1)))
        
        total_power = base_power + wealth_power + corporation_influence
        
        return min(total_power, 100)  # Cap at 100
    
    def calculate_monopoly_power(self, corporation_market_share: float) -> float:
        """
        Calculate monopoly power using Herfindahl-Hirschman Index (HHI)
        HHI > 2500 = highly concentrated (monopolistic)
        """
        # Market share as percentage squared
        hhi = (corporation_market_share * 100) ** 2
        
        # Normalize to 0-1 scale
        monopoly_power = hhi / 10000
        
        return monopoly_power
    
    def calculate_welfare_payment(self, server_data: Dict, 
                                 economic_class: EconomicClass,
                                 unemployment_status: bool) -> float:
        """Calculate welfare/unemployment benefits"""
        if not CLASS_BENEFITS[economic_class]["welfare_eligible"]:
            return 0
            
        base_payment = server_data["settings"]["welfare_amount"]
        
        if unemployment_status:
            # Unemployment benefits are higher
            return base_payment * 2
            
        return base_payment
    
    def calculate_gdp_growth(self, current_gdp: float, previous_gdp: float) -> float:
        """Calculate GDP growth rate"""
        if previous_gdp <= 0:
            return 0
            
        growth_rate = ((current_gdp - previous_gdp) / previous_gdp) * 100
        return growth_rate
    
    def simulate_market_volatility(self, base_volatility: float = 0.10) -> float:
        """Generate realistic market volatility using stochastic processes"""
        # Mean-reverting volatility (GARCH-like)
        shock = random.gauss(0, base_volatility)
        persistence = 0.85
        
        volatility = persistence * base_volatility + (1 - persistence) * abs(shock)
        
        return max(0.01, min(volatility, 0.50))
    
    def optimize_portfolio(self, available_funds: float, 
                          risk_tolerance: float) -> Dict[str, float]:
        """
        Modern Portfolio Theory - optimize investment allocation
        Maximize return for given risk level
        """
        allocations = {}
        remaining_funds = available_funds
        
        # Sort investments by Sharpe ratio (return/risk)
        investments_sorted = sorted(
            INVESTMENT_TYPES.items(),
            key=lambda x: x[1]["annual_return"] / max(x[1]["risk"], 0.01),
            reverse=True
        )
        
        for inv_type, inv_data in investments_sorted:
            if remaining_funds < inv_data["min_amount"]:
                continue
                
            # Allocate based on risk tolerance
            if inv_data["risk"] <= risk_tolerance:
                allocation = min(remaining_funds * 0.3, remaining_funds)
                allocations[inv_type] = allocation
                remaining_funds -= allocation
                
            if remaining_funds < 100:
                break
                
        return allocations
    
    def calculate_redistribution_effect(self, total_wealth: float,
                                       gini_coefficient: float,
                                       tax_rate: float) -> Dict:
        """
        Calculate effects of wealth redistribution
        Returns new Gini coefficient and social stability
        """
        # Tax revenue for redistribution
        tax_revenue = total_wealth * tax_rate
        
        # Redistribution reduces inequality
        gini_reduction = tax_rate * 0.5
        new_gini = max(0, gini_coefficient - gini_reduction)
        
        # Social stability improves with lower inequality
        stability = 1.0 - new_gini
        
        return {
            "new_gini": new_gini,
            "stability": stability,
            "redistributed_amount": tax_revenue
        }
    
    def calculate_productivity(self, skill_level: int, 
                              job_experience: int,
                              economic_phase: str) -> float:
        """Calculate worker productivity multiplier"""
        base_productivity = 1.0
        
        # Skill contribution
        skill_factor = 1.0 + (skill_level * 0.05)
        
        # Experience contribution (diminishing returns)
        experience_factor = 1.0 + math.log10(max(job_experience + 1, 1)) * 0.1
        
        # Economic cycle effect
        cycle_factor = PHASE_MODIFIERS[economic_phase]["gdp_growth"]
        
        productivity = base_productivity * skill_factor * experience_factor * cycle_factor
        
        return min(productivity, 3.0)  # Cap at 3x
