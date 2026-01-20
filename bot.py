import discord
from discord.ext import commands, tasks
from logic import DatabaseManager, hide_img
from config import TOKEN, DATABASE
import os

ADMIN_ID = 123456789012345678  # KENDİ DISCORD ID’Nİ YAZ

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

manager = DatabaseManager(DATABASE)
manager.create_tables()

# ================= START =================
@bot.command()
async def start(ctx):
    manager.add_user(ctx.author.id, ctx.author.name)
    await ctx.send("Kaydoldun! Açık artırmaya hazırsın 🎉")

# ================= BONUS =================
@bot.command()
async def bonus(ctx):
    b = manager.get_bonus(ctx.author.id)
    await ctx.send(f"⭐ Bonus puanın: {b}")

@bot.command()
async def give_bonus(ctx, member: discord.Member, amount: int):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("Bu komutu sadece admin kullanabilir.")
        return
    manager.add_bonus(member.id, amount)
    await ctx.send(f"{member.name} kullanıcısına {amount} bonus verildi.")

# ================= AÇIK ARTIRMA =================
@tasks.loop(minutes=1)
async def send_message():
    prize = manager.get_random_prize()
    if not prize:
        return

    prize_id, img = prize
    hide_img(img)

    for user_id in manager.get_users():
        user = await bot.fetch_user(user_id)
        if user:
            await send_image(user, f'hidden_img/{img}', prize_id)

    manager.mark_prize_used(prize_id)

async def send_image(user, image_path, prize_id):
    with open(image_path, "rb") as f:
        file = discord.File(f)
        button = discord.ui.Button(label="Al!", custom_id=str(prize_id))
        view = discord.ui.View()
        view.add_item(button)
        await user.send(file=file, view=view)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        prize_id = int(interaction.data["custom_id"])
        user_id = interaction.user.id

        if manager.add_winner(user_id, prize_id):
            manager.add_bonus(user_id, 2)
            img = manager.get_prize_img(prize_id)
            with open(f'img/{img}', 'rb') as f:
                await interaction.response.send_message(
                    content="🎉 Kazandın! +2 bonus",
                    file=discord.File(f)
                )
        else:
            manager.add_bonus(user_id, 1)
            await interaction.response.send_message(
                content="Kaçırdın ama +1 bonus kazandın ⭐",
                ephemeral=True
            )

@bot.event
async def on_ready():
    print("Bot çalışıyor!")
    if not send_message.is_running():
        send_message.start()

bot.run(TOKEN)
