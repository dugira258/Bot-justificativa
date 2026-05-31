import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import asyncio

# ---------------------- CONFIGURAÇÕES ----------------------
TOKEN = "COLOQUE_SEU_TOKEN_AQUI" # <-- COLOCA SEU TOKEN AQUI ENTRE AS ASPAS

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

# ---------------------- EVENTO QUANDO LIGA ----------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE como: {bot.user}")
    # Sincroniza os comandos (ISSO FAZ APARECER OS COMANDOS!)
    try:
        synced = await tree.sync()
        print(f"🔄 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")

# ---------------------- COMANDOS DE CONFIGURAÇÃO ----------------------

@tree.command(name="configcanal", description="Define os canais do sistema")
@app_commands.describe(tipo="Escolha: painel, solicitação ou histórico", canal="Mencione o canal")
async def configcanal(interaction: discord.Interaction, tipo: str, canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    tipos_validos = ["painel", "solicitação", "histórico"]
    if tipo.lower() not in tipos_validos:
        return await interaction.response.send_message("❌ Tipo inválido! Use: painel, solicitação ou histórico", ephemeral=True)

    if "canais" not in config:
        config["canais"] = {}
    config["canais"][tipo.lower()] = canal.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de **{tipo}** definido: {canal.mention}")


@tree.command(name="painelconfig", description="Define o cargo que aprova justificativas")
async def painelconfig(interaction: discord.Interaction, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    config["cargo_aprovador"] = cargo.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Cargo aprovador: {cargo.mention}")


@tree.command(name="configver", description="Mostra todas as configurações")
async def configver(interaction: discord.Interaction):
    canais = config.get("canais", {})
    cargo_id = config.get("cargo_aprovador")
    cargo = interaction.guild.get_role(cargo_id) if cargo_id else "Não definido"

    embed = discord.Embed(title="⚙️ Configurações", color=discord.Color.blurple())
    embed.add_field(name="📌 Canais", value=f"Painel: <#{canais.get('painel','❌')}>\nSolicitações: <#{canais.get('solicitação','❌')}>\nHistórico: <#{canais.get('histórico','❌')}>", inline=False)
    embed.add_field(name="👤 Aprovador", value=cargo.mention if isinstance(cargo,discord.Role) else cargo, inline=False)
    await interaction.response.send_message(embed=embed)


@tree.command(name="limparhistorico", description="Apaga todo o histórico de justificativas")
async def limparhistorico(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    global historico
    historico = {}
    salvar_dados(HISTORICO_FILE, historico)
    await interaction.response.send_message("✅ Histórico limpo!")


# ---------------------- PERSONALIZAÇÃO DO PAINEL ----------------------

@tree.command(name="título", description="Muda o título do painel")
async def titulo(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    config["titulo"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Título: `{texto}`")


@tree.command(name="descrição", description="Muda a descrição do painel")
async def descricao(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    config["descricao"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message("✅ Descrição salva!")


@tree.command(name="tumber", description="Coloca imagem no painel")
async def tumber(interaction: discord.Interaction, link: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    config["imagem"] = link
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message("✅ Imagem definida!")


# ---------------------- SISTEMA DE PAINEL E FORMULÁRIO ----------------------

class FormJustificativa(discord.ui.Modal, title="📝 Enviar Justificativa"):
    nick = discord.ui.TextInput(label="NICK", required=True)
    id_user = discord.ui.TextInput(label="ID", required=True)
    acao = discord.ui.TextInput(label="AÇÃO", required=True)
    motivo = discord.ui.TextInput(label="MOTIVO", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        dados = {
            "nick": self.nick.value,
            "id": self.id_user.value,
            "acao": self.acao.value,
            "motivo": self.motivo.value,
            "status": "pendente",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        # Enviar para canal de solicitações
        canal_sol = bot.get_channel(config["canais"]["solicitação"])
        cargo_id = config.get("cargo_aprovador")

        embed = discord.Embed(title="📩 Nova Solicitação", color=discord.Color.yellow())
        embed.add_field(name="👤 Nome", value=dados["nick"], inline=True)
        embed.add_field(name="🆔 ID", value=dados["id"], inline=True)
        embed.add_field(name="⚡ Ação", value=dados["acao"], inline=False)
        embed.add_field(name="📝 Motivo", value=dados["motivo"], inline=False)

        # Botões de aprovar/recusar
        class Botoes(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.green, emoji="✅")
            async def aceitar(self, inter: discord.Interaction, btn: discord.ui.Button):
                if not inter.user.guild_permissions.administrator and (cargo_id not in [r.id for r in inter.user.roles]):
                    return await inter.response.send_message("❌ Não pode!", ephemeral=True)

                dados["status"] = "aceita"
                historico[dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                # Avisar no PV
                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"✅ Sua justificativa foi ACEITA!\nMotivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await inter.response.edit_message(content="✅ ACEITO", embed=embed, view=None)

            @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, emoji="❌")
            async def recusar(self, inter: discord.Interaction, btn: discord.ui.Button):
                if not inter.user.guild_permissions.administrator and (cargo_id not in [r.id for r in inter.user.roles]):
                    return await inter.response.send_message("❌ Não pode!", ephemeral=True)

                dados["status"] = "recusada"
                historico[dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"❌ Sua justificativa foi RECUSADA!\nMotivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await inter.response.edit_message(content="❌ RECUSADO", embed=embed, view=None)

        await canal_sol.send(embed=embed, view=Botoes())
        await interaction.response.send_message("✅ Enviado! Aguarde análise.", ephemeral=True)


@tree.command(name="painel", description="Mostra o painel principal")
async def painel(interaction: discord.Interaction):
    canal_painel = config.get("canais", {}).get("painel")
    if interaction.channel.id != canal_painel:
        return await interaction.response.send_message("❌ Só funciona no canal do Painel!", ephemeral=True)

    titulo = config.get("titulo", "📋 Sistema de Justificativas")
    desc = config.get("descricao", "Clique abaixo para enviar")
    img = config.get("imagem", None)

    embed = discord.Embed(title=titulo, description=desc, color=discord.Color.green())
    if img: embed.set_thumbnail(url=img)

    class ViewPainel(discord.ui.View):
        @discord.ui.button(label="Enviar Justificativa", style=discord.ButtonStyle.green, emoji="📝")
        async def abrir(self, inter: discord.Interaction, btn: discord.ui.Button):
            await inter.response.send_modal(FormJustificativa())

    await interaction.response.send_message(embed=embed, view=ViewPainel())


# ---------------------- ATUALIZAR HISTÓRICO ----------------------
async def atualizar_historico(guild):
    canal_hist = bot.get_channel(config["canais"]["histórico"])
    await canal_hist.purge(limit=100)

    texto = ""
    for dado in historico.values():
        if dado["status"] == "aceita":
            texto += f"`{dado['nick']}` | ✅️ - aceita\n"
        elif dado["status"] == "recusada":
            texto += f"`{dado['nick']}` | ❌️ - recusada\n"
        else:
            texto += f"`{dado['nick']}` | 🕝 - pendente\n"

    embed = discord.Embed(title="📜 Histórico", description=texto or "Nenhuma justificativa", color=discord.Color.blurple())
    await canal_hist.send(embed=embed)


# ---------------------- RODAR BOT ----------------------
bot.run(os.environ['TOKEN'])
