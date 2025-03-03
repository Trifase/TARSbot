import json
import random
import re
from configparser import ConfigParser

import aiohttp
from pyrogram import Client, enums, filters

import openai


async def openai_response(engine, prompt, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, client, message):
    try:
        await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)

        cfg = ConfigParser(interpolation=None)
        cfg.read("config.ini")
        openai_apikeys = cfg.items("openai_apikeys")
        api_key = random.choice(list(openai_apikeys))[1]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.openai.com/v1/engines/{engine}/completions", headers=headers, json=payload) as resp:
                resp_json = await resp.json()
                return resp_json
    except Exception as e:
        await message.reply(f"Error: {e}")
        await client.send_message(chat_id=int(cfg["admins"]["admin1"]), text=f"Broken OpenAI API key: {api_key[-5:]}")


@Client.on_message(filters.regex(r"(?i)^!ask(\w+)"))
async def ask(client, message):
    engine = re.match(r"(?i)^!ask(\w+)", message.text).group(1).lower()
    prompt = message.text[1+3+len(engine)+1:]

    if engine == "davinci":
        cfg = ConfigParser(interpolation=None)
        cfg.read("config.ini")
        premium_users_str = cfg.get("openai_premium_users", "ids")
        premium_users = [int(id) for id in premium_users_str.split(", ")]
        
        if message.from_user.id in premium_users:
            response = await openai_response("text-davinci-003", prompt, 0.9, 300, 1, 0, 0.6, client, message)
            await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.reply("Sorry, you're not premium. Register on openai.com and send the `API key` using `!apikey <apikey>`. It's free!\n\nAlternatively, use `!askcurie`. It's less intelligent but it gets the job done.")

    elif engine == "curie":
        response = await openai_response("text-curie-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
        await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)

    elif engine == "babbage":
        response = await openai_response("text-babbage-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
        await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)

    elif engine == "ada":
        response = await openai_response("text-ada-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
        await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)

    else:
        await message.reply(
            text="Usage:\n"
            "• `!askdavinci <text>` - the smartest engine (requires premium, infos down below)\n"
            "• `!askcurie <text>`\n"
            "• `!askbabbage <text>`\n"
            "• `!askada <text>` - the least intelligent engine\n\n"
            "**Premium (actually it's FREE!):**\n"
            "The DaVinci engine requires more computational power and is more intelligent than the others. It's free to use, but you need to register an account on openai.com and send the `API key` using `!apikey <apikey>`. This won't cost you anything, you don't even need credit cards or anything like that.",
            parse_mode=enums.ParseMode.MARKDOWN
        )


@Client.on_message(filters.command("chat", "!"))
async def startchat(client, message):
    if len(message.command) == 1:
        await message.reply(
            text="Usage: `!chat <role> & <prompt>`\n\n"
            "Use \"`&`\" to separate the role from the prompt. If you don't specify a role, the default one will be used.\n\n"
            "Example: `!chat You're a funny and witty assistant. & Hello, how are you?`",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
        
        cfg = ConfigParser(interpolation=None)
        cfg.read("config.ini")
        openai_apikeys = cfg.items("openai_apikeys")
        api_key = random.choice(list(openai_apikeys))[1]
        openai.api_key = api_key

        default_role = "You're TARS. a helpful and friendly assistant, always ready to help people, whatever they ask you to do. Your pronouns are they/them."
        input_text = message.text[1+4+1:]
        if "&" in input_text:
            role, prompt = input_text.split("&")
        else:
            role = default_role
            prompt = message.text[1+4+1:]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt},
                ],
            }
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data),
            ) as response:
                response_data = await response.json()

        response_text = response_data["choices"][0]["message"]["content"]
        await message.reply(response_text)


@Client.on_message(filters.text & filters.reply, group=2)
async def continue_chat(client, message):
    if message.reply_to_message.from_user.id == client.me.id:        
        cfg = ConfigParser(interpolation=None)
        cfg.read("config.ini")
        openai_apikeys = cfg.items("openai_apikeys")
        api_key = random.choice(list(openai_apikeys))[1]
        openai.api_key = api_key

        if message.reply_to_message.text:
            prompt = message.text
        elif message.reply_to_message.caption:
            prompt = message.caption
        else:
            return
        
        default_role = "You're TARS, a helpful and friendly assistant, always ready to help people, whatever they ask you to do. Your pronouns are they/them."
        first_response = message.reply_to_message
        first_response_text = first_response.text
        first_prompt = first_response.reply_to_message
        first_prompt_text = first_prompt.text
        if not first_prompt_text.startswith("!chat"):
            return

        await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)

        if "&" in first_prompt_text:
            role, first_prompt_text = first_prompt_text.split("&")
        else:
            role = default_role

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": role},
                    {"role": "user", "content": first_prompt_text},
                    {"role": "assistant", "content": first_response_text},
                    {"role": "user", "content": prompt},
                ],
            }
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data),
            ) as response:
                response_data = await response.json()
        
        response_text = response_data["choices"][0]["message"]["content"]
        await message.reply(response_text)

        # if message.from_user.id == 14770193:
        #     await message.reply(role)
        #     await message.reply(first_prompt_text)
        #     await message.reply(first_response_text)
        #     await message.reply(prompt)



@Client.on_message(filters.command("continue", "!"))
async def continue_text(client, message):
    usage = ("Usage: `!continue <engine>` in reply to a text message.\n\n"
             "Availvable engines:\n"
            "• `davinci` (requires premium, use `!ask` to learn more\n"
            "• `curie`\n"
            "• `babbage`\n"
            "• `ada`")
    
    if len(message.command) == 1 or len(message.command) >= 3 and not message.reply_to_message.text:
        await message.reply(text=usage, parse_mode=enums.ParseMode.MARKDOWN)

    else:
        if message.reply_to_message.text:
            prompt = message.reply_to_message.text
        elif message.reply_to_message.caption:
            prompt = message.reply_to_message.caption
        else:
            prompt = f"Write a story about {message.from_user.first_name} shitting his pants."
            
        if message.command[1].lower() == "davinci":
            cfg = ConfigParser(interpolation=None)
            cfg.read("config.ini")
            premium_users_str = cfg.get("openai_premium_users", "ids")
            premium_users = [int(id) for id in premium_users_str.split(", ")]
            
            if message.from_user.id in premium_users:
                response = await openai_response("text-davinci-003", prompt, 0.9, 300, 1, 0, 0.6, client, message)
                await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)
            else:
                await message.reply("Sorry, you're not premium. Register on openai.com and send the `API key` using `!apikey <apikey>`. It's free!\n\nAlternatively, use `!askcurie`. It's less intelligent but it gets the job done.")
        
        elif message.command[1].lower() == "curie":
            response = await openai_response("text-curie-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
            await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)
        
        elif message.command[1].lower() == "babbage":
            response = await openai_response("text-babbage-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
            await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)

        elif message.command[1].lower() == "ada":
            response = await openai_response("text-ada-001", prompt, 0.9, 300, 1, 0, 0.6, client, message)
            await message.reply(text=f"**{prompt}**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)

        else:
            await message.reply(text=usage, parse_mode=enums.ParseMode.MARKDOWN)


@Client.on_message(filters.command("face", "!"))
async def face(client, message):
    await message.reply("This command is currently disabled due to a server error. The developer is working on a fix.")


@Client.on_message(filters.command("faceai", "!"))
async def faceai(client, message):
    await message.reply("This command is currently disabled due to a server error. The developer is working on a fix.")


@Client.on_message(filters.command("apikey", ["!", "/"]))
async def apikey(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")

    if len(message.command) == 1:
        await message.reply(text="Usage: `!apikey <apikey>`", parse_mode=enums.ParseMode.MARKDOWN)
        await client.send_message(chat_id=int(cfg["admins"]["admin1"]), text=f"Invalid API key from {message.from_user.first_name} (`{message.from_user.id}`):\n\n`{message.text}`", parse_mode=enums.ParseMode.MARKDOWN)
    else:
        if len(message.command[1]) == 51:
            try:
                # headers = {
                #     "Content-Type": "application/json",
                #     "Authorization": f"Bearer {message.command[1]}"
                # }
                # payload = {
                #     "prompt": "Tell me a fun fact:",
                #     "max_tokens": 50,
                #     "temperature": 0.9,
                #     "top_p": 1,
                #     "frequency_penalty": 0,
                #     "presence_penalty": 0
                # }

                # async with aiohttp.ClientSession() as session:
                #     async with session.post("https://api.openai.com/v1/engines/text-ada-001/completions", headers=headers, data=json.dumps(payload)) as response:
                #         response = await response.json()

                openai.api_key = message.command[1]
                response = openai.Completion.create(
                    engine="text-ada-001",
                    prompt="Tell me a fun fact:",
                    max_tokens=50, temperature=0.9, top_p=1, frequency_penalty=0, presence_penalty=0
                )
            except Exception:
                await message.reply(text="I tested the API key you sent and it doesn't seem to work. These are the possible reasons:\n- it could be expired (if you registered more than 3 months ago on openai.com);\n- there's no more credit left on the account;\n- the API key is invalid;\n- the servers are currently down, try again later.")
                await client.send_message(chat_id=int(cfg["admins"]["admin1"]), text=f"Invalid API key from {message.from_user.first_name} (`{message.from_user.id}`):\n\n`{message.text}`", parse_mode=enums.ParseMode.MARKDOWN)
                return

            from datetime import datetime
            user_id = str(message.from_user.id)
            date = datetime.today().strftime('%d%m%Y')
            apikey = message.command[1]

            ids = cfg.get('openai_premium_users', 'ids')
            cfg.set('openai_premium_users', 'ids', f"{ids}, {user_id}")
            cfg.set("openai_apikeys", f"{user_id}_{date}", apikey)

            with open("config.ini", "w") as configfile:
                cfg.write(configfile)

            await message.reply(text="API key set successfully! You can now use `!askdavinci` and `!continue davinci` to get more advanced responses.")
            await client.send_message(chat_id=int(cfg["admins"]["admin1"]), text=f"New API key from {message.from_user.first_name} (`{message.from_user.id}`):\n\n`{message.command[1]}`\n\nTest Response:\n**Tell me a fun fact:**{response['choices'][0]['text']}", parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await client.send_message(chat_id=int(cfg["admins"]["admin1"]), text=f"Invalid API key from {message.from_user.first_name} (`{message.from_user.id}`):\n\n`{message.command[1]}`", parse_mode=enums.ParseMode.MARKDOWN)
            if message.command[1].startswith("org-"):
                await message.reply(text="You copied the wrong key. After logging in on openai.com, click on your profile picture in the top right corner, then click on **View API Keys**. You'll see a key that starts with `sk-`, copy that one.", parse_mode=enums.ParseMode.MARKDOWN)
            else:
                await message.reply(text="Invalid API key. After logging in on openai.com, click on your profile picture in the top right corner, then click on **View API Keys**. You'll see a key that starts with `sk-`, copy that one.", parse_mode=enums.ParseMode.MARKDOWN)


@Client.on_message(filters.command("addpremium", "!"))
async def addpremium(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")

    if len(message.command) == 1:
        await message.reply(text="Usage: `!addpremium <user_id> <date in ggmmyyyy> <apikey>`", parse_mode=enums.ParseMode.MARKDOWN)
    else:
        if message.from_user.id == int(cfg["admins"]["admin1"]):
            user_id = message.command[1]
            date = message.command[2]
            apikey = message.command[3]

            ids = cfg.get('openai_premium_users', 'ids')
            cfg.set('openai_premium_users', 'ids', f"{ids}, {user_id}")
            cfg.set("openai_apikeys", f"{user_id}_{date}", apikey)

            with open("config.ini", "w") as configfile:
                cfg.write(configfile)
            
            await message.reply(text="Premium user added.")


@Client.on_message(filters.command("apikeys", "!"))
async def apikeys(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")

    if message.from_user.id == int(cfg["admins"]["admin1"]):
        apikeys = cfg.items("openai_apikeys")
        apikeys_str = ""

        for i, key in enumerate(apikeys, start=1):
            apikeys_str += f"{i}. `{key[0]}` = `{key[1]}`\n\n"
        
        await message.reply(text=f"{apikeys_str}", parse_mode=enums.ParseMode.MARKDOWN)


@Client.on_message(filters.command("delapikey", "!"))
async def delapikey(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")

    if len(message.command) == 1:
        await message.reply(text="Usage: `!delapikey <index>`", parse_mode=enums.ParseMode.MARKDOWN)
    else:
        if message.from_user.id == int(cfg["admins"]["admin1"]):
            apikeys = cfg.items("openai_apikeys")
            index = int(message.command[1])

            if index <= len(apikeys):
                cfg.remove_option("openai_apikeys", apikeys[index-1][0])

                with open("config.ini", "w") as configfile:
                    cfg.write(configfile)
                
                await message.reply(text="API key deleted.")
            else:
                await message.reply(text="Invalid index.")


@Client.on_message(filters.command("testapikey", "!"))
async def testapikey(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")

    if len(message.command) == 1:
        await message.reply(text="Usage: `!testapikey <apikey>`", parse_mode=enums.ParseMode.MARKDOWN)
    else:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {message.command[1]}"
            }
            payload = {
                "prompt": "Tell me a fun fact:",
                "max_tokens": 50,
                "temperature": 0.9,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.openai.com/v1/engines/text-ada-001/completions", headers=headers, data=json.dumps(payload)) as response:
                    response = await response.json()           
                    await message.reply(text=response, parse_mode=enums.ParseMode.MARKDOWN)

        except KeyError as e:
            await message.reply(f"Error: `{e}`", parse_mode=enums.ParseMode.MARKDOWN)


@Client.on_message(filters.command("openaihelp", "!"))
async def openaihelp(client, message):
    cfg = ConfigParser(interpolation=None)
    cfg.read("config.ini")
    
    if message.from_user.id == int(cfg["admins"]["admin1"]):
        await message.reply("OpenAI admin commands:\n\n"
                            "• `!addpremium <user_id> <date in ggmmyyyy> <apikey>`\n"
                            "• `!apikeys`\n"
                            "• `!delapikey <index>`\n"
                            "• `!testapikey <apikey>`\n",
                            parse_mode=enums.ParseMode.MARKDOWN
        )
