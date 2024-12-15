#(©)CodeXBotz

import pymongo, os
from config import DB_URI, DB_NAME

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
user_data = database['users']

async def present_user(user_id : int):
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