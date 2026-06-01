import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import asyncio
import os
from keep_alive import keep_alive

# ---------------------- CONFIGURAÇÕES ----------------------
TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Arquivos de dados
CONFIG_FILE = "config.json"
HISTORICO_FILE = "historico.json"

# Carregar dados
def carregar_dados(arquivo):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

config = carregar_dados(CONFIG_FILE)
historico = carregar_dados(HISTORICO_FILE)


# ✅ FUNÇÃO PARA MANTER ELE ACORDADO
@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE como: {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔄 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")

    # Loop infinito para manter ele ligado
    while True:
        await asyncio.sleep(300)


# ---------------------- COMANDOS DE CONFIGURAÇÃO (SEPARADO POR SERVIDOR) ----------------------

@tree.command(name="configcanal", description="Define os canais do sistema")
@app_commands.describe(tipo="Escolha: painel, solicitação ou histórico", canal="Mencione o canal ou cole o ID")
async def configcanal(interaction: discord.Interaction, tipo: str, canal: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    tipos_validos = ["painel", "solicitação", "histórico"]
    if tipo.lower() not in tipos_validos:
        return await interaction.response.send_message("❌ Tipo inválido! Use: painel, solicitação ou histórico", ephemeral=True)

    # Tenta pegar o canal pelo ID ou menção
    try:
        canal_id = int(canal.strip("<>#"))
        canal_obj = bot.get_channel(canal_id)
        if not canal_obj:
            return await interaction.response.send_message("❌ Canal não encontrado ou o bot não tem acesso a ele!", ephemeral=True)
    except:
        return await interaction.response.send_message("❌ ID do canal inválido! Copie o ID correto do canal.", ephemeral=True)

    # SALVA POR SERVIDOR
    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    if "canais" not in config[guild_id]:
        config[guild_id]["canais"] = {}

    config[guild_id]["canais"][tipo.lower()] = canal_obj.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de **{tipo}** definido: {canal_obj.mention}")


@tree.command(name="painelconfig", description="Define o cargo que aprova justificativas")
async def painelconfig(interaction: discord.Interaction, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["cargo_aprovador"] = cargo.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Cargo aprovador: {cargo.mention}")


@tree.command(name="configver", description="Mostra todas as configurações")
async def configver(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})
    cargo_id = dados_guild.get("cargo_aprovador")
    cargo = interaction.guild.get_role(cargo_id) if cargo_id else "Não definido"

    embed = discord.Embed(title="⚙️ Configurações", color=discord.Color.blurple())
    embed.add_field(name="📌 Canais", value=f"Painel: <#{canais.get('painel','❌')}>\nSolicitações: <#{canais.get('solicitação','❌')}>\nHistórico: <#{canais.get('histórico','❌')}>", inline=False)
    embed.add_field(name="👤 Aprovador", value=cargo.mention if isinstance(cargo,discord.Role) else cargo, inline=False)
    await interaction.response.send_message(embed=embed)


@tree.command(name="limparhistorico", description="Apaga todo o histórico de justificativas")
async def limparhistorico(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id in historico:
        del historico[guild_id]
        salvar_dados(HISTORICO_FILE, historico)
    await interaction.response.send_message("✅ Histórico limpo!")


# ---------------------- PERSONALIZAÇÃO DO PAINEL ----------------------

@tree.command(name="título", description="Muda o título do painel")
async def titulo(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["titulo"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Título: `{texto}`")


@tree.command(name="descrição", description="Muda a descrição do painel")
async def descricao(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["descricao"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message("✅ Descrição salva!")


@tree.command(name="tumber", description="Coloca imagem no painel")
async def tumber(interaction: discord.Interaction, link: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["imagem"] = link
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message("✅ Imagem definida!")


# ---------------------- SISTEMA DE PAINEL E FORMULÁRIO (CORRIGIDO PARA FUNCIONAR SEMPRE) ----------------------

class FormJustificativa(discord.ui.Modal, title="📝 Enviar Justificativa"):
    nick = discord.ui.TextInput(label="NICK", required=True)
    id_user = discord.ui.TextInput(label="ID", required=True)
    acao = discord.ui.TextInput(label="AÇÃO", required=True)
    motivo = discord.ui.TextInput(label="MOTIVO", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        dados_guild = config.get(guild_id, {})
        canais = dados_guild.get("canais", {})
        cargo_id = dados_guild.get("cargo_aprovador")

        # ✅ Verifica se está tudo configurado ANTES
        if "solicitação" not in canais or "histórico" not in canais:
            return await interaction.response.send_message("❌ Primeiro configure os canais com /configcanal", ephemeral=True)

        dados = {
            "nick": self.nick.value,
            "id": self.id_user.value,
            "acao": self.acao.value,
            "motivo": self.motivo.value,
            "status": "pendente",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        canal_sol = bot.get_channel(canais["solicitação"])
        if not canal_sol:
            return await interaction.response.send_message("❌ Canal de solicitação não existe ou sem acesso!", ephemeral=True)

        embed = discord.Embed(title="📩 Nova Solicitação", color=discord.Color.yellow())
        embed.add_field(name="👤 Nome", value=dados["nick"], inline=True)
        embed.add_field(name="🆔 ID", value=dados["id"], inline=True)
        embed.add_field(name="⚡ Ação", value=dados["acao"], inline=False)
        embed.add_field(name="📝 Motivo", value=dados["motivo"], inline=False)

        # ✅ BOTÕES COM FUNÇÃO PERSISTENTE — NÃO EXPIRA MAIS!
        class Botoes(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)  # <-- ESSA LINHA FAZ FICAR PRA SEMPRE

            @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.green, emoji="✅", custom_id="btn_aceitar")
            async def aceitar(self, inter: discord.Interaction, btn: discord.ui.Button):
                if not inter.user.guild_permissions.administrator and (cargo_id not in [r.id for r in inter.user.roles]):
                    return await inter.response.send_message("❌ Você não tem permissão para aprovar!", ephemeral=True)

                dados["status"] = "aceita"
                if guild_id not in historico:
                    historico[guild_id] = {}
                historico[guild_id][dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"✅ Sua justificativa foi **ACEITA**!\n📌 Motivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await inter.response.edit_message(content="✅ **SOLICITAÇÃO ACEITA**", embed=embed, view=None)

            @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, emoji="❌", custom_id="btn_recusar")
            async def recusar(self, inter: discord.Interaction, btn: discord.ui.Button):
                if not inter.user.guild_permissions.administrator and (cargo_id not in [r.id for r in inter.user.roles]):
                    return await inter.response.send_message("❌ Você não tem permissão para recusar!", ephemeral=True)

                dados["status"] = "recusada"
                if guild_id not in historico:
                    historico[guild_id] = {}
                historico[guild_id][dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"❌ Sua justificativa foi **RECUSADA**!\n📌 Motivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await inter.response.edit_message(content="❌ **SOLICITAÇÃO RECUSADA**", embed=embed, view=None)


        await canal_sol.send(embed=embed, view=Botoes())
        await interaction.response.send_message("✅ Enviado! Aguarde análise da equipe.", ephemeral=True)


@tree.command(name="painel", description="Mostra o painel principal")
async def painel(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        dados_guild = config.get(guild_id, {})
        canais = dados_guild.get("canais", {})

        if "painel" not in canais or interaction.channel.id != canais["painel"]:
            return await interaction.response.send_message("❌ Só pode ser usado no canal definido como Painel desse servidor!", ephemeral=True)

        titulo = dados_guild.get("titulo", "📋 Sistema de Justificativas")
        desc = dados_guild.get("descricao", "📌 **JUSTIFICA SUA FALTA COM CLAREZA** 🚀\n\n✅ Informe obrigatoriamente seu **NICK**, **ID** e o **MOTIVO** da justificativa.\n✅ Seja claro, direto e objetivo, sem enrolação.\n✅ É obrigatório informar qual foi a **AÇÃO** realizada (ex: kick, ban, advertência etc.).")
        img = dados_guild.get("imagem", None)

        embed = discord.Embed(title=titulo, description=desc, color=discord.Color.green())
        if img: embed.set_thumbnail(url=img)

        # ✅ PAINEL COM BOTÃO PERSISTENTE — NÃO PARA DE FUNCIONAR NUNCA MAIS!
        class ViewPainel(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)  # <-- CHAVE PARA FUNCIONAR SEMPRE

            @discord.ui.button(label="📝 Enviar Justificativa", style=discord.ButtonStyle.green, custom_id="btn_abrir_form")
            async def abrir(self, inter: discord.Interaction, btn: discord.ui.Button):
                await inter.response.send_modal(FormJustificativa())

        await interaction.response.send_message(embed=embed, view=ViewPainel())


# ---------------------- ATUALIZAR HISTÓRICO ----------------------
async def atualizar_historico(guild):
    guild_id = str(guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})
    canal_hist = bot.get_channel(canais.get("histórico"))
    if not canal_hist: return

    await canal_hist.purge(limit=100)

    texto = ""
    historico_guild = historico.get(guild_id, {})
    for dado in historico_guild.values():
        if dado["status"] == "aceita":
            texto += f"`{dado['nick']}` | ✅ **ACEITA** | {dado['data']}\n"
        elif dado["status"] == "recusada":
            texto += f"`{dado['nick']}` | ❌ **RECUSADA** | {dado['data']}\n"
        else:
            texto += f"`{dado['nick']}` | 🕒 **PENDENTE** | {dado['data']}\n"

    embed = discord.Embed(title="📜 Histórico de Justificativas", description=texto or "📌 Nenhuma justificativa registrada ainda.", color=discord.Color.blurple())
    await canal_hist.send(embed=embed)


# ---------------------- RODAR BOT ----------------------
keep_alive()
bot.run(TOKEN)
