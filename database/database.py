# (©)CodeXBotz

import pymongo
import os
from config import DB_URI, DB_NAME
import motor.motor_asyncio
from config import JOIN_REQS_DB
from pyrogram.types import ChatJoinRequest
from datetime import datetime

# MongoDB Client and User Data Operations
dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
user_data = database['users']

async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return


# Join Requests Class
class JoinReqs:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(JOIN_REQS_DB)
        self.db = self.client["FSUB_CHANNEL"]
        self.col = self.db["join_requests"]

    def is_active(self):
        return self.client is not None

    def get_collection(self):
        if not self.is_active():
            print("Error: Database connection is not active.")
            return None
        return self.col

    async def add_user(self, user_id, channel_id, first_name, username):
        self.col = self.get_collection()
        if self.col is None:
            print(f"Error: Collection not found for join requests.")
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
            await self.col.update_one(
                {"user_id": int(user_id), "channel_id": int(channel_id)},
                {"$set": request},
                upsert=True
            )
            print(f"Join request for user {user_id} added to channel {channel_id}.")
        except Exception as e:
            print(f"Error adding join request: {e}")

    async def get_join_request(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return None
        try:
            return await self.col.find_one({"user_id": int(user_id), "channel_id": int(channel_id)})
        except Exception as e:
            print(f"Error retrieving join request for user {user_id} in channel {channel_id}: {e}")
            return None

    async def check_existing_request(self, user_id, channel_id):
        request = await self.get_join_request(user_id, channel_id)
        if request:
            if request['status'] == 'pending':
                print(f"User {user_id} already has a pending request for channel {channel_id}.")
                return True
            else:
                print(f"User {user_id} has a completed request (status: {request['status']}) for channel {channel_id}.")
                return True
        else:
            print(f"No join request found for user {user_id} in channel {channel_id}.")
            return False

    async def has_join_request(self, user_id, channel_id):
        request = await self.get_join_request(user_id, channel_id)
        return request is not None

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
            return await self.col.find().to_list(None)
        except Exception as e:
            print(f"Error retrieving all users: {e}")
            return []

    async def delete_user(self, user_id, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return
        try:
            await self.col.delete_one({"user_id": int(user_id), "channel_id": int(channel_id)})
            print(f"User {user_id} removed from channel {channel_id}.")
        except Exception as e:
            print(f"Error deleting user {user_id} from channel {channel_id}: {e}")

    async def delete_all_users(self, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return
        try:
            await self.col.delete_many({"channel_id": int(channel_id)})
            print(f"All join requests removed from channel {channel_id}.")
        except Exception as e:
            print(f"Error deleting all users from channel {channel_id}: {e}")

    async def get_all_users_count1(self, channel_id):
        self.col = self.get_collection()
        if self.col is None:
            return 0
        try:
            return await self.col.count_documents({"channel_id": int(channel_id)})
        except Exception as e:
            print(f"Error counting users in channel {channel_id}: {e}")
            return 0

    async def get_fsub_mode(self, channel_id):
        self.col = self.db["fsub_modes"]
        try:
            doc = await self.col.find_one({"channel_id": channel_id})
            if doc and "mode" in doc:
                return doc["mode"] if doc["mode"] in ["direct", "request"] else "direct"
            else:
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
            if result.matched_count > 0:
                print(f"FSUB mode for Channel {channel_id} updated to `{mode}`.")
            else:
                print(f"FSUB mode for Channel {channel_id} set to `{mode}` (new document).")
        except Exception as e:
            print(f"Error setting FSUB mode for channel {channel_id}: {e}")