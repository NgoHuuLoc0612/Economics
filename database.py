"""
Database Models and Schemas
MongoDB document structures for the Economics Bot
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
from config import *
import asyncio

class Database:
    """
    Enterprise-grade database handler for Economics Bot
    Manages all MongoDB operations with proper indexing and transactions
    """
    
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        
        # Collections
        self.users = self.db.users
        self.servers = self.db.servers
        self.transactions = self.db.transactions
        self.corporations = self.db.corporations
        self.loans = self.db.loans
        self.investments = self.db.investments
        self.crimes = self.db.crimes
        self.elections = self.db.elections
        self.laws = self.db.laws
        self.strikes = self.db.strikes
        self.market_history = self.db.market_history
        self.events = self.db.events
        
    async def initialize_indexes(self):
        """Create all necessary indexes for optimal query performance"""
        await self.users.create_index([("user_id", 1), ("guild_id", 1)], unique=True)
        await self.users.create_index([("guild_id", 1), ("balance", -1)])
        await self.users.create_index([("guild_id", 1), ("economic_class", 1)])
        
        await self.servers.create_index([("guild_id", 1)], unique=True)
        
        await self.transactions.create_index([("guild_id", 1), ("timestamp", -1)])
        await self.transactions.create_index([("from_user", 1)])
        await self.transactions.create_index([("to_user", 1)])
        
        await self.corporations.create_index([("guild_id", 1)])
        await self.corporations.create_index([("owner_id", 1)])
        
        await self.loans.create_index([("user_id", 1), ("guild_id", 1)])
        await self.loans.create_index([("due_date", 1)])
        
        await self.investments.create_index([("user_id", 1), ("guild_id", 1)])
        
        await self.crimes.create_index([("user_id", 1), ("guild_id", 1)])
        await self.crimes.create_index([("timestamp", -1)])
        
        await self.elections.create_index([("guild_id", 1), ("active", 1)])
        
        await self.market_history.create_index([("guild_id", 1), ("timestamp", -1)])
        
    async def get_user(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Get or create user profile"""
        user = await self.users.find_one({"user_id": user_id, "guild_id": guild_id})
        
        if not user:
            user = {
                "user_id": user_id,
                "guild_id": guild_id,
                "balance": 1000,
                "bank": 0,
                "economic_class": EconomicClass.LOWER.value,
                "job": "unemployed",
                "skill_level": 0,
                "experience": 0,
                "salary": 0,
                "last_daily": None,
                "last_weekly": None,
                "last_monthly": None,
                "last_work": None,
                "inventory": {},
                "investments": [],
                "loans": [],
                "crime_record": [],
                "jail_until": None,
                "political_power": 1,
                "union_member": False,
                "corporation_id": None,
                "achievements": [],
                "reputation": 0,
                "created_at": datetime.utcnow(),
                "statistics": {
                    "total_earned": 1000,
                    "total_spent": 0,
                    "crimes_committed": 0,
                    "crimes_success": 0,
                    "jobs_worked": 0,
                    "taxes_paid": 0,
                    "loans_taken": 0,
                    "investments_made": 0
                }
            }
            await self.users.insert_one(user)
            
        return user
    
    async def update_user(self, user_id: int, guild_id: int, update_data: Dict[str, Any]):
        """Update user data"""
        await self.users.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": update_data}
        )
    
    async def get_server(self, guild_id: int) -> Dict[str, Any]:
        """Get or create server economy"""
        server = await self.servers.find_one({"guild_id": guild_id})
        
        if not server:
            server = {
                "guild_id": guild_id,
                "settings": DEFAULT_SERVER_SETTINGS.copy(),
                "gdp": 0,
                "gdp_growth": 0,
                "total_money_supply": 0,
                "inflation_rate": 0.02,
                "unemployment_rate": 0.05,
                "gini_coefficient": 0.0,
                "cycle_phase": "expansion",
                "cycle_start": datetime.utcnow(),
                "interest_rate": 0.05,
                "min_wage": 1500,
                "tax_revenue": 0,
                "government_budget": 0,
                "active_laws": [],
                "political_positions": {
                    "mayor": None,
                    "treasurer": None,
                    "police_chief": None,
                    "labor_secretary": None,
                    "central_banker": None
                },
                "market_prices": {item: data["base_price"] for item, data in BASE_ITEMS.items()},
                "job_market": {job: {"employed": 0, "wage_multiplier": 1.0} for job in JOBS.keys()},
                "active_events": [],
                "crime_rate": 0.05,
                "strike_active": False,
                "last_update": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            await self.servers.insert_one(server)
            
        return server
    
    async def update_server(self, guild_id: int, update_data: Dict[str, Any]):
        """Update server data"""
        await self.servers.update_one(
            {"guild_id": guild_id},
            {"$set": update_data}
        )
    
    async def record_transaction(self, guild_id: int, from_user: int, to_user: int, 
                                amount: float, transaction_type: str, metadata: Dict = None):
        """Record a transaction for economic tracking"""
        transaction = {
            "guild_id": guild_id,
            "from_user": from_user,
            "to_user": to_user,
            "amount": amount,
            "type": transaction_type,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        await self.transactions.insert_one(transaction)
    
    async def get_leaderboard(self, guild_id: int, sort_by: str = "balance", limit: int = 10) -> List[Dict]:
        """Get server leaderboard"""
        cursor = self.users.find({"guild_id": guild_id}).sort(sort_by, -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_class_distribution(self, guild_id: int) -> Dict[str, int]:
        """Get distribution of users across economic classes"""
        pipeline = [
            {"$match": {"guild_id": guild_id}},
            {"$group": {"_id": "$economic_class", "count": {"$sum": 1}}}
        ]
        result = await self.users.aggregate(pipeline).to_list(length=None)
        return {item["_id"]: item["count"] for item in result}
    
    async def calculate_gini_coefficient(self, guild_id: int) -> float:
        """Calculate Gini coefficient for wealth inequality"""
        users = await self.users.find(
            {"guild_id": guild_id},
            {"balance": 1, "bank": 1}
        ).to_list(length=None)
        
        if len(users) < 2:
            return 0.0
        
        wealth = sorted([u["balance"] + u["bank"] for u in users])
        n = len(wealth)
        
        cumsum = sum((i + 1) * w for i, w in enumerate(wealth))
        return (2 * cumsum) / (n * sum(wealth)) - (n + 1) / n
    
    async def get_gdp(self, guild_id: int, days: int = 7) -> float:
        """Calculate GDP based on transactions"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        pipeline = [
            {"$match": {"guild_id": guild_id, "timestamp": {"$gte": cutoff}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await self.transactions.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0.0
    
    async def create_loan(self, user_id: int, guild_id: int, amount: float, 
                         interest_rate: float, duration_days: int) -> Dict:
        """Create a loan for a user"""
        loan = {
            "user_id": user_id,
            "guild_id": guild_id,
            "principal": amount,
            "interest_rate": interest_rate,
            "remaining": amount * (1 + interest_rate),
            "due_date": datetime.utcnow() + timedelta(days=duration_days),
            "created_at": datetime.utcnow(),
            "defaulted": False
        }
        result = await self.loans.insert_one(loan)
        loan["_id"] = result.inserted_id
        return loan
    
    async def get_active_loans(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all active loans for a user"""
        cursor = self.loans.find({
            "user_id": user_id,
            "guild_id": guild_id,
            "remaining": {"$gt": 0},
            "defaulted": False
        })
        return await cursor.to_list(length=None)
    
    async def create_investment(self, user_id: int, guild_id: int, 
                               investment_type: str, amount: float) -> Dict:
        """Create an investment"""
        investment = {
            "user_id": user_id,
            "guild_id": guild_id,
            "type": investment_type,
            "principal": amount,
            "current_value": amount,
            "created_at": datetime.utcnow(),
            "last_update": datetime.utcnow()
        }
        result = await self.investments.insert_one(investment)
        investment["_id"] = result.inserted_id
        return investment
    
    async def get_user_investments(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all investments for a user"""
        cursor = self.investments.find({"user_id": user_id, "guild_id": guild_id})
        return await cursor.to_list(length=None)
    
    async def create_corporation(self, owner_id: int, guild_id: int, 
                                name: str, corp_type: str) -> Dict:
        """Create a corporation"""
        corporation = {
            "owner_id": owner_id,
            "guild_id": guild_id,
            "name": name,
            "type": corp_type,
            "balance": 0,
            "employees": [owner_id],
            "revenue": 0,
            "expenses": 0,
            "influence": CORPORATION_BENEFITS[corp_type]["influence"],
            "created_at": datetime.utcnow()
        }
        result = await self.corporations.insert_one(corporation)
        corporation["_id"] = result.inserted_id
        return corporation
    
    async def get_corporation(self, corp_id: str) -> Optional[Dict]:
        """Get corporation by ID"""
        from bson import ObjectId
        return await self.corporations.find_one({"_id": ObjectId(corp_id)})
    
    async def create_election(self, guild_id: int, position: str, 
                             candidates: List[int], duration_hours: int = 24) -> Dict:
        """Create an election"""
        election = {
            "guild_id": guild_id,
            "position": position,
            "candidates": candidates,
            "votes": {str(c): 0 for c in candidates},
            "voters": [],
            "active": True,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=duration_hours)
        }
        result = await self.elections.insert_one(election)
        election["_id"] = result.inserted_id
        return election
    
    async def get_active_election(self, guild_id: int, position: str) -> Optional[Dict]:
        """Get active election for a position"""
        return await self.elections.find_one({
            "guild_id": guild_id,
            "position": position,
            "active": True
        })
    
    async def record_crime(self, user_id: int, guild_id: int, crime_type: str, 
                          success: bool, amount: float, victim_id: Optional[int] = None):
        """Record a crime attempt"""
        crime = {
            "user_id": user_id,
            "guild_id": guild_id,
            "crime_type": crime_type,
            "success": success,
            "amount": amount,
            "victim_id": victim_id,
            "timestamp": datetime.utcnow()
        }
        await self.crimes.insert_one(crime)
    
    async def get_crime_rate(self, guild_id: int, hours: int = 24) -> float:
        """Calculate crime rate"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        total_crimes = await self.crimes.count_documents({
            "guild_id": guild_id,
            "timestamp": {"$gte": cutoff}
        })
        
        total_users = await self.users.count_documents({"guild_id": guild_id})
        
        return total_crimes / max(total_users, 1)
    
    async def create_law(self, guild_id: int, law_name: str, description: str, 
                        effects: Dict, creator_id: int) -> Dict:
        """Create a new law"""
        law = {
            "guild_id": guild_id,
            "name": law_name,
            "description": description,
            "effects": effects,
            "creator_id": creator_id,
            "active": True,
            "created_at": datetime.utcnow()
        }
        result = await self.laws.insert_one(law)
        law["_id"] = result.inserted_id
        return law
    
    async def get_active_laws(self, guild_id: int) -> List[Dict]:
        """Get all active laws"""
        cursor = self.laws.find({"guild_id": guild_id, "active": True})
        return await cursor.to_list(length=None)
    
    async def create_strike(self, guild_id: int, job: str, organizer_id: int, 
                           demands: str) -> Dict:
        """Create a labor strike"""
        strike = {
            "guild_id": guild_id,
            "job": job,
            "organizer_id": organizer_id,
            "demands": demands,
            "supporters": [organizer_id],
            "active": True,
            "created_at": datetime.utcnow()
        }
        result = await self.strikes.insert_one(strike)
        strike["_id"] = result.inserted_id
        return strike
    
    async def get_active_strike(self, guild_id: int) -> Optional[Dict]:
        """Get active strike"""
        return await self.strikes.find_one({"guild_id": guild_id, "active": True})
    
    async def record_market_snapshot(self, guild_id: int, data: Dict):
        """Record market state for historical tracking"""
        snapshot = {
            "guild_id": guild_id,
            "timestamp": datetime.utcnow(),
            "data": data
        }
        await self.market_history.insert_one(snapshot)
    
    async def get_unemployment_rate(self, guild_id: int) -> float:
        """Calculate unemployment rate"""
        total = await self.users.count_documents({"guild_id": guild_id})
        unemployed = await self.users.count_documents({
            "guild_id": guild_id,
            "job": "unemployed"
        })
        return unemployed / max(total, 1)
