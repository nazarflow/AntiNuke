import time
from src import database

class RateLimiter:
    def __init__(self):
        # Structure: {guild_id: {user_id: {"channels": [timestamp1, ...], "roles": [...], "links": [...], "webhooks": [...]}}}
        self.tracker = {}

    def clean_old_records(self):
        """Removes records older than the maximum possible time window (e.g. 1 hour)."""
        current_time = time.time()
        max_age = 3600  # 1 hour in seconds
        
        for guild_id, users in list(self.tracker.items()):
            for user_id, actions in list(users.items()):
                for action_type, timestamps in list(actions.items()):
                    actions[action_type] = [t for t in timestamps if current_time - t <= max_age]
                    if not actions[action_type]:
                        del actions[action_type]
                if not actions:
                    del users[user_id]
            if not users:
                del self.tracker[guild_id]

    def add_action(self, guild_id: int, user_id: int, action_type: str):
        """Records an action timestamp for a user."""
        if guild_id not in self.tracker:
            self.tracker[guild_id] = {}
        if user_id not in self.tracker[guild_id]:
            self.tracker[guild_id][user_id] = {}
        if action_type not in self.tracker[guild_id][user_id]:
            self.tracker[guild_id][user_id][action_type] = []
            
        self.tracker[guild_id][user_id][action_type].append(time.time())

    def check_limit(self, guild_id: int, user_id: int, action_type: str, user_roles: list) -> bool:
        """
        Checks if a user has exceeded their limits for a specific action.
        Returns True if the user is ALLOWED (not rate-limited).
        Returns False if the user exceeded the limit (should be punished).
        """
        # Fetch all custom admin roles in the guild
        custom_roles_ids = database.get_all_custom_roles(guild_id)
        
        # Determine the user's best limits
        best_limit = 0
        best_time = 0
        
        has_custom_role = False
        
        for role in user_roles:
            if role.id in custom_roles_ids:
                has_custom_role = True
                limits = database.get_custom_role_limits(role.id)
                if limits:
                    r_limit = limits.get(f"{action_type}_limit", 0)
                    r_time = limits.get(f"{action_type}_time", 0)
                    
                    # If any role grants unlimited (e.g. we might define -1 as unlimited), handle it here
                    # For now, we take the maximum limit
                    if r_limit > best_limit:
                        best_limit = r_limit
                        best_time = r_time
        
        if not has_custom_role:
            # If the user has no custom roles, they have NO limits (i.e. 0 allowed actions)
            # Alternatively, we could fallback to `guild_limits` default values.
            # But the user said "0 0 means forbidden". If they don't have an admin role, they are forbidden.
            return False
            
        if best_limit == 0:
            return False  # Forbidden completely
            
        # Check against local tracker
        if guild_id in self.tracker and user_id in self.tracker[guild_id] and action_type in self.tracker[guild_id][user_id]:
            timestamps = self.tracker[guild_id][user_id][action_type]
            current_time = time.time()
            
            # Count how many actions occurred within 'best_time' (which is in minutes)
            window_seconds = best_time * 60
            recent_actions = [t for t in timestamps if current_time - t <= window_seconds]
            
            # Update tracker to only keep recent actions
            self.tracker[guild_id][user_id][action_type] = recent_actions
            
            if len(recent_actions) > best_limit:
                return False  # Exceeded limit
                
        return True

# Singleton instance to be imported across the bot
limiter = RateLimiter()
