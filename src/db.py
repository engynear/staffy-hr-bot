import asyncpg
from aiogram import types

from aiogram.fsm.context import FSMContext

class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn

    async def create_tables(self):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER UNIQUE PRIMARY KEY,
                        name TEXT,
                        username TEXT
                    );
                ''')

                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS states (
                        id SERIAL PRIMARY KEY,
                        telegram_id INTEGER UNIQUE,
                        state JSONB
                    );
                ''')

                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS teams (
                        id SERIAL PRIMARY KEY,
                        team_name TEXT UNIQUE,
                        team_description TEXT
                    );
                ''')

                #create team_members table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        id SERIAL PRIMARY KEY,
                        team_id INTEGER,
                        user_id INTEGER UNIQUE
                    );
                ''')

                #create wishes table: id, from_user_id, to_user_id, wish_text, datetime
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS wishes (
                        id SERIAL PRIMARY KEY,
                        from_user_id INTEGER,
                        to_user_id INTEGER,
                        wish_text TEXT,
                        datetime TIMESTAMP
                    );
                ''')

    # drop tables
    async def drop_tables(self):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('DROP TABLE IF EXISTS users;')
                await conn.execute('DROP TABLE IF EXISTS states;')
                await conn.execute('DROP TABLE IF EXISTS teams;')
                await conn.execute('DROP TABLE IF EXISTS team_members;')
                await conn.execute('DROP TABLE IF EXISTS wishes;')
                

    # add user
    async def add_user(self, user: types.User):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''INSERT INTO users (id, name, username)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        username = EXCLUDED.username;
                ''', user.id, user.full_name, user.username)

    #update user
    async def update_user(self, user_id: int, name: str):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''UPDATE users
                    SET name = $1
                    WHERE id = $2
                ''', name, user_id)

    # get user
    async def get_user(self, user_id: int):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
                if row:
                    return row
                else:
                    return None

    # get users
    async def get_users(self):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM users')
                return rows

    # add team
    async def add_team(self, team_name: str, team_description: str):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''INSERT INTO teams (team_name, team_description)
                    VALUES ($1, $2)
                    ON CONFLICT (team_name) DO UPDATE SET
                        team_description = EXCLUDED.team_description;
                ''', team_name, team_description)
    
    # get team
    async def get_team(self, team_name: str):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM teams WHERE team_name = $1', team_name)
                if row:
                    return row
                else:
                    return None

    # get user team
    async def get_user_team(self, user_id: int):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM team_members WHERE user_id = $1', user_id)
                if row:
                    team_id = row['team_id']
                    team = await conn.fetchrow('SELECT * FROM teams WHERE id = $1', team_id)
                    return team
                else:
                    return None

    # add team member
    async def add_team_member(self, team_id: int, user_id: int):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO team_members (team_id, user_id)
                    VALUES ($1, $2)
                ''', team_id, user_id)

    # get team members
    async def get_team_members(self, team_id: int):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                #return list of users in team
                rows = await conn.fetch('SELECT * FROM team_members WHERE team_id = $1', team_id)

                team_members = []
                for row in rows:
                    user_id = row['user_id']
                    user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
                    team_members.append(user)
                return team_members

    # add wish from user to user, wish text, datetime
    async def add_wish(self, from_user_id: int, to_user_id: int, wish_text: str):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO wishes (from_user_id, to_user_id, wish_text, datetime)
                    VALUES ($1, $2, $3, NOW())
                ''', from_user_id, to_user_id, wish_text)
    
    # get wishes for user after now() - 7 days
    async def get_last_week_wishes(self, user_id: int):
        async with asyncpg.create_pool(self.dsn) as pool:
            async with pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM wishes
                    WHERE to_user_id = $1 AND datetime > NOW() - INTERVAL '7 days'
                ''', user_id)

                return rows


async def get_db() -> Database:
    import os
    dsn = os.environ.get('DATABASE_URL')
    return Database(dsn)