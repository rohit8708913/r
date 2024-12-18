import motor.motor_asyncio
from datetime import datetime
from pyrogram.types import ChatJoinRequest
from config import JOIN_REQS_DB

FSUB_CHANNEL = None  # Default value if not set
FSUB_ENABLED = True  # Change dynamically using commands

class JoinReqs:
    def __init__(self, db_name="FSUB_CHANNEL"):
        try:
            # Connect to MongoDB
            self.client = motor.motor_asyncio.AsyncIOMotorClient(JOIN_REQS_DB)
            self.db = self.client[db_name]
            self.col = self.db["join_requests"]
            print("Database connected successfully.")
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.client = None
            self.db = None
            self.col = None

    def is_active(self):
        return self.client is not None

    def get_collection(self):
        if not self.is_active():
            print("Error: Database connection is not active.")
            return None
        return self.col

    async def add_user1(self, user_id, channel_id, first_name, username):
        self.col = self.get_collection()
        if self.col is None:
            print("Error: Collection not found for join requests.")
            return
        existing_request = await self.get_join_request(user_id, channel_id)
        if existing_request and existing_request.get("status") == "pending":
            print(f"User {user_id} already has a pending request for channel {channel_id}. Skipping addition.")
            return
        try:
            request = {
                "user_id": int(user_id),
                "channel_id": int(channel_id),
                "first_name": first_name,
                "username": username,
                "date": datetime.now(),
                "status": "pending",
            }
            # Avoid overwriting existing data unless it's a valid request
            if not existing_request:
                result = await self.col.insert_one(request)
                print(f"Inserted new join request: {result.inserted_id}")
            else:
                result = await self.col.update_one(
                    {"user_id": int(user_id), "channel_id": int(channel_id)},
                    {"$set": request}
                )
                print(f"Updated existing join request: {result.matched_count}")
        except Exception as e:
            print(f"Error adding join request: {e}")

    async def get_join_request(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            print("Error: Collection not found for join requests.")
            return None
        try:
            print(f"Fetching join request for user_id={user_id}, channel_id={channel_id}")
            result = await self.col.find_one({"user_id": int(user_id), "channel_id": int(channel_id)})
            if result:
                print(f"Join request found: {result}")
            else:
                print(f"No join request found for user_id={user_id}, channel_id={channel_id}.")
            return result
        except Exception as e:
            print(f"Error retrieving join request for user {user_id} in channel {channel_id}: {e}")
            return None

    async def has_join_request(self, user_id, channel_id):
        request = await self.get_join_request(user_id, channel_id)
        return request is not None

    async def check_existing_request(self, user_id, channel_id):
        request = await self.get_join_request(user_id, channel_id)
        if request:
            if request.get('status') == 'pending':
                print(f"User {user_id} already has a pending request for channel {channel_id}.")
                return True
            else:
                print(f"User {user_id} has a completed request (status: {request['status']}).")
                return True
        print(f"No join request found for user {user_id} in channel {channel_id}.")
        return False

    async def approve_join_request(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return
        try:
            await self.col.update_one(
                {"user_id": int(user_id), "channel_id": int(channel_id)},
                {"$set": {"status": "approved"}}
            )
            print(f"Join request for user {user_id} in channel {channel_id} approved.")
        except Exception as e:
            print(f"Error approving join request: {e}")

    async def reject_join_request(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return
        try:
            await self.col.update_one(
                {"user_id": int(user_id), "channel_id": int(channel_id)},
                {"$set": {"status": "rejected"}}
            )
            print(f"Join request for user {user_id} in channel {channel_id} rejected.")
        except Exception as e:
            print(f"Error rejecting join request: {e}")

    async def remove_join_request(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return
        try:
            await self.col.delete_one({"user_id": int(user_id), "channel_id": int(channel_id)})
            print(f"Join request for user {user_id} removed from channel {channel_id}.")
        except Exception as e:
            print(f"Error removing join request for user {user_id} in channel {channel_id}: {e}")

    async def get_all_users(self):
        self.col = self.get_collection()
        if self.col is None:
            return []
        try:
            users = await self.col.find().to_list(None)
            print(f"Retrieved all users: {users}")
            return users
        except Exception as e:
            print(f"Error retrieving all users: {e}")
            return []

    async def get_all_users_count(self, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return 0
        try:
            count = await self.col.count_documents({"channel_id": int(channel_id)})
            print(f"User count for channel {channel_id}: {count}")
            return count
        except Exception as e:
            print(f"Error counting users in channel {channel_id}: {e}")
            return 0

    async def delete_all_users(self, channel_id):  # Accept channel_id as an argument
        self.col = self.get_collection()
        if self.col is None:
            print("Error: Collection not found for join requests.")
            return
        try:
            result = await self.col.delete_many({"channel_id": channel_id})
            print(f"Deleted all users for channel {channel_id}: {result.deleted_count} document(s) removed.")
        except Exception as e:
            print(f"Error deleting all users for channel {channel_id}: {e}")

    async def get_fsub_mode(self, channel_id):
        self.col = self.db["fsub_modes"]
        try:
            doc = await self.col.find_one({"channel_id": channel_id})
            if doc and "mode" in doc:
                mode = doc["mode"] if doc["mode"] in ["direct", "request"] else "direct"
                print(f"FSUB mode for channel {channel_id}: {mode}")
                return mode
            else:
                print("No FSUB mode found, defaulting to 'direct'")
                return "direct"
        except Exception as e:
            print(f"Error getting FSUB mode for channel {channel_id}: {e}")
            return "direct"

    async def set_fsub_mode(self, channel_id, mode):
        self.col = self.db["fsub_modes"]
        try:
            result = await self.col.update_one(
                {"channel_id": channel_id},
                {"$set": {"mode": mode}},
                upsert=True
            )
            print(f"FSUB mode for Channel {channel_id} set to `{mode}`.")
        except Exception as e:
            print(f"Error setting FSUB mode for channel {channel_id}: {e}")

    async def create_chat_invite_link1(self, client, channel_id):
        """Create an invite link for the channel."""
        try:
            link = await client.create_chat_invite_link(channel_id, creates_join_request=True)
            print(f"Created invite link: {link.invite_link}")
            return link.invite_link
        except Exception as e:
            print(f"Error creating invite link for Channel {channel_id}: {e}")
            return None

    async def get_user(self, user_id):
        return await self.col.find_one({"user_id": int(user_id)})