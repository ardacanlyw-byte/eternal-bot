import os
import json
import datetime
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# --- RENDER PORT UYARISINI ÇÖZMEK İÇİN WEB SUNUCUSU ---
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()
# -----------------------------------------------------

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)

PARTNERS_FILE = "partners.json"

def load_partner_data():
    if not os.path.exists(PARTNERS_FILE):
        return {"daily": 0, "weekly": 0, "total": 0, "last_reset_day": datetime.datetime.utcnow().day}
    with open(PARTNERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"daily": 0, "weekly": 0, "total": 0, "last_reset_day": datetime.datetime.utcnow().day}

def save_partner_data(data):
    with open(PARTNERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

warnings_db = {}

@bot.event
async def on_ready():
    print(f'{bot.user} aktif ve çalışıyor!')
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} adet slash komutu senkronize edildi.")
    except Exception as e:
        print(e)

# --- LOG SİSTEMLERİ ---

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_channel = discord.utils.get(message.guild.text_channels, name="︰꒷❗・log")
    if log_channel:
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
        embed.add_field(name="Yazar", value=message.author.mention, inline=True)
        embed.add_field(name="İçerik", value=message.content or "İçerik yok (Medya vb.)", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    log_channel = discord.utils.get(before.guild.text_channels, name="︰꒷❗・log")
    if log_channel:
        embed = discord.Embed(title="✏️ Mesaj Düzenlendi", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Kanal", value=before.channel.mention, inline=True)
        embed.add_field(name="Yazar", value=before.author.mention, inline=True)
        embed.add_field(name="Eski", value=before.content, inline=False)
        embed.add_field(name="Yeni", value=after.content, inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name="︰꒷❗・log")
    if log_channel:
        embed = discord.Embed(title="🔨 Kullanıcı Yasaklandı (Ban)", color=discord.Color.dark_red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Kullanıcı", value=f"{user} ({user.id})", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name="︰꒷❗・log")
    if log_channel:
        embed = discord.Embed(title="🔓 Yasak Kaldırıldı (Unban)", color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Kullanıcı", value=f"{user} ({user.id})", inline=False)
        await log_channel.send(embed=embed)

# --- PARTNER SİSTEMİ ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name == "╰꒷🌼・partners":
        if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
            data = load_partner_data()
            current_day = datetime.datetime.utcnow().day
            if data.get("last_reset_day") != current_day:
                data["daily"] = 0
                data["last_reset_day"] = current_day

            data["daily"] += 1
            data["weekly"] += 1
            data["total"] += 1
            save_partner_data(data)

            embed = discord.Embed(color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name="Partner Record", icon_url=message.author.display_avatar.url)
            embed.description = f"| {message.author.mention} sent a partner message!"
            
            embed.add_field(name="📅 Today", value=f"{data['daily']} partner", inline=False)
            embed.add_field(name="📊 This Week", value=f"{data['weekly']} partner", inline=False)
            embed.add_field(name="🏆 All Time", value=f"{data['total']} partner", inline=False)
            
            embed.set_footer(text=f"ID: {message.id}")
            await message.channel.send(embed=embed)

    await bot.process_commands(message)


# --- MODERN YARDIM KOMUTU (/help) ---
@bot.tree.command(name="help", description="Botun modern kategorize edilmiş komut listesini gösterir.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ Eternal Bot - Komut Menüsü",
        description="Aşağıdan botun tüm moderasyon, uyarı, sohbet ve bilgi komutlarına göz atabilirsin.",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    embed.add_field(
        name="🛡️ Üye İşlemleri (Moderasyon)",
        value=(
            "`/ban` - Kullanıcıyı kalıcı yasaklar.\n"
            "`/tempban` - Süreli yasaklar.\n"
            "`/unban` - Yasak kaldırma.\n"
            "`/kick` - Kullanıcıyı atar.\n"
            "`/mute` / `/tempmute` - Susturma işlemleri.\n"
            "`/unmute` - Susturmayı kaldırır."
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚠️ Uyarı ve İhlal Yönetimi",
        value=(
            "`/warn` - Kullanıcıya uyarı verir.\n"
            "`/infractions` - Uyarı geçmişini gösterir.\n"
            "`/clear-all-infractions` - Tüm uyarıları temizler."
        ),
        inline=False
    )
    
    embed.add_field(
        name="💬 Sohbet ve Bilgi Komutları",
        value=(
            "`/clear` - Toplu mesaj siler.\n"
            "`/slowmode` - Yavaş mod ayarlar.\n"
            "`/user-info` - Kullanıcı bilgisi gösterir.\n"
            "`/role-info` - Rol bilgisi gösterir.\n"
            "`/server-info` - Sunucu bilgisi gösterir."
        ),
        inline=False
    )
    
    embed.set_footer(text=f"İsteyen: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- ÜYE İŞLEMLERİ (SLASH KOMUTLARI) ---

@bot.tree.command(name="ban", description="Kullanıcıyı sunucudan kalıcı yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"Başarıyla yasaklandı: {member.mention}", ephemeral=True)

@bot.tree.command(name="kick", description="Kullanıcıyı sunucudan atar.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"Başarıyla atıldı: {member.mention}", ephemeral=True)

@bot.tree.command(name="unban", description="Kullanıcının yasaklamasını kaldırır.")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"Yasak kaldırıldı: {user}", ephemeral=True)

@bot.tree.command(name="mute", description="Kullanıcıyı süresiz susturur (Timeout).")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Sebep yok"):
    duration = datetime.timedelta(days=27)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"{member.mention} susturuldu.", ephemeral=True)

@bot.tree.command(name="tempmute", description="Kullanıcıyı belirli süreliğine susturur (dakika cinsinden).")
@app_commands.checks.has_permissions(moderate_members=True)
async def tempmute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Sebep yok"):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"{member.mention} {minutes} dakika süreyle susturuldu.", ephemeral=True)

@bot.tree.command(name="unmute", description="Kullanıcının susturmasını kaldırır.")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"{member.mention} adlı kullanıcının susturması kaldırıldı.", ephemeral=True)


# --- UYARI VE İHLAL YÖNETİMİ ---

@bot.tree.command(name="warn", description="Kullanıcıya uyarı verir.")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    uid = member.id
    if uid not in warnings_db:
        warnings_db[uid] = []
    warnings_db[uid].append(reason)
    await interaction.response.send_message(f"{member.mention} uyarıldı. Sebep: {reason}", ephemeral=True)

@bot.tree.command(name="infractions", description="Kullanıcının uyarı geçmişini gösterir.")
@app_commands.checks.has_permissions(manage_messages=True)
async def infractions(interaction: discord.Interaction, member: discord.Member):
    uid = member.id
    user_warns = warnings_db.get(uid, [])
    if not user_warns:
        await interaction.response.send_message(f"{member.mention} için hiç uyarı kaydı bulunmuyor.", ephemeral=True)
    else:
        text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(user_warns)])
        embed = discord.Embed(title=f"{member.name} - Uyarı Geçmişi", description=text, color=discord.Color.yellow())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="clear-all-infractions", description="Kullanıcının tüm ihlal kayıtlarını temizler.")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all_infractions(interaction: discord.Interaction, member: discord.Member):
    if member.id in warnings_db:
        del warnings_db[member.id]
    await interaction.response.send_message(f"{member.mention} adlı kullanıcısının tüm uyarıları temizlendi.", ephemeral=True)


# --- SOHBET VE BİLGİ KOMUTLARI ---

@bot.tree.command(name="clear", description="Kanaldaki mesajları toplu olarak siler.")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"{len(deleted)} adet mesaj silindi.", ephemeral=True)

@bot.tree.command(name="slowmode", description="Kanal için yavaş mod süresini saniye cinsinden ayarlar.")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Yavaş mod {seconds} olarak ayarlandı.", ephemeral=True)

@bot.tree.command(name="user-info", description="Kullanıcı hakkında bilgi gösterir.")
async def user_info(interaction: discord.Interaction, member: discord.Member = None):
    m = member or interaction.user
    embed = discord.Embed(title=f"Kullanıcı Bilgisi: {m.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=m.id, inline=True)
    embed.add_field(name="Kayıt Tarihi", value=m.created_at.strftime("%d-%m-%Y"), inline=True)
    embed.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="server-info", description="Sunucunda sunucu hakkında bilgi gösterir.")
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Sunucu Bilgisi: {guild.name}", color=discord.Color.purple())
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(name="Kuruluş Tarihi", value=guild.created_at.strftime("%d-%m-%Y"), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="role-info", description="Rol hakkında bilgi gösterir.")
async def role_info(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(title=f"Rol Bilgisi: {role.name}", color=role.color)
    embed.add_field(name="Rol ID", value=role.id, inline=True)
    embed.add_field(name="Üye Sayısı", value=len(role.members), inline=True)
    await interaction.response.send_message(embed=embed)

# Flask sunucusunu başlat ve botu çalıştır
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
