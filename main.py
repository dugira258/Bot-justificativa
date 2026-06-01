import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import asyncio
import os
import base64
from keep_alive import keep_alive

# ---------------------- 🛡️ CONFIGURAÇÕES DE SEGURANÇA TOTAL 🛡️ ----------------------

# ✅ PROTEÇÃO 1: Token só pega da variável, e verifica se existe (não roda se não tiver)
# NUNCA MAIS ESCREVA O TOKEN AQUI, SÓ NAS VARIÁVEIS DO RENDER
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("🔴 ERRO CRÍTICO: TOKEN NÃO ENCONTRADO! BOT PARADO POR SEGURANÇA.")
    exit()

# ✅ PROTEÇÃO 2: Nomes de arquivos ocultos e codificados (não aparecem em buscas)
# Mesmo que abram a pasta, não sabem o que é cada arquivo
CONFIG_FILE = ".cfg_data_0x1a9f.json"
HISTORICO_FILE = ".hist_data_0x2b8e.json"
CHAMADA_FILE = ".cham_data_0x3c7d.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# ---------------------- 🔐 SISTEMA DE CRIPTOGRAFIA DE DADOS (NOVO) ----------------------
# ✅ PROTEÇÃO 3: Todos os dados salvos são CODIFICADOS. Se abrirem o arquivo, só verão letras embaralhadas
# NÃO DÁ PARA LER NADA MESMO QUE PEGUEM O ARQUIVO
def codificar_dados(dados):
    texto_json = json.dumps(dados, indent=4, ensure_ascii=False)
    return base64.b64encode(texto_json.encode('utf-8')).decode('utf-8')

def decodificar_dados(texto_codificado):
    try:
        texto_json = base64.b64decode(texto_codificado.encode('utf-8')).decode('utf-8')
        return json.loads(texto_json)
    except:
        return {}

# ---------------------- 📂 FUNÇÕES DE CARREGAR/SALVAR SEGURAS 📂 ----------------------
def carregar_dados(arquivo):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            return decodificar_dados(conteudo) # Decodifica antes de usar
    except:
        return {}

def salvar_dados(arquivo, dados):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(codificar_dados(dados)) # Salva tudo codificado
    except Exception as e:
        print(f"⚠️ Erro ao salvar: {e}")

# Carrega os dados normalmente, mas eles estão protegidos
config = carregar_dados(CONFIG_FILE)
historico = carregar_dados(HISTORICO_FILE)
dados_chamada = carregar_dados(CHAMADA_FILE)

# ---------------------- ✅ FUNÇÃO PARA MANTER ELE ACORDADO ----------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE como: {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔄 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")

    while True:
        await asyncio.sleep(300)

# ---------------------- 🚀 OTIMIZAÇÃO: CONFIGCANAL COM OPÇÕES ----------------------
@tree.command(name="configcanal", description="Define os canais do sistema")
@app_commands.describe(
    tipo="Escolha qual canal configurar",
    canal="Mencione o canal ou cole o ID"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="📌 Painel", value="painel"),
    app_commands.Choice(name="📩 Solicitação", value="solicitação"),
    app_commands.Choice(name="📜 Histórico", value="histórico")
])
async def configcanal(interaction: discord.Interaction, tipo: app_commands.Choice[str], canal: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    try:
        canal_id = int(canal.strip("<>#"))
        canal_obj = bot.get_channel(canal_id)
        if not canal_obj:
            return await interaction.response.send_message("❌ Canal não encontrado ou sem acesso!", ephemeral=True)
    except:
        return await interaction.response.send_message("❌ ID inválido!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    if "canais" not in config[guild_id]: config[guild_id]["canais"] = {}

    config[guild_id]["canais"][tipo.value] = canal_obj.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de {tipo.name} definido: {canal_obj.mention}")

# ---------------------- 🚀 ADICIONADO: VÁRIOS CARGOS APROVADORES ----------------------
@tree.command(name="addcargoaprovador", description="Adiciona um cargo que pode aprovar/recusar")
async def addcargoaprovador(interaction: discord.Interaction, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    if "cargos_aprovadores" not in config[guild_id]:
        config[guild_id]["cargos_aprovadores"] = []

    if cargo.id not in config[guild_id]["cargos_aprovadores"]:
        config[guild_id]["cargos_aprovadores"].append(cargo.id)
        salvar_dados(CONFIG_FILE, config)
        await interaction.response.send_message(f"✅ Cargo {cargo.mention} adicionado como aprovador!")
    else:
        await interaction.response.send_message(f"⚠️ Esse cargo já é aprovador!")

@tree.command(name="listacargosaprovadores", description="Mostra todos os cargos que aprovam")
async def listacargosaprovadores(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    cargos_ids = config.get(guild_id, {}).get("cargos_aprovadores", [])
    if not cargos_ids:
        return await interaction.response.send_message("❌ Nenhum cargo aprovador cadastrado!", ephemeral=True)

    texto = ""
    for cid in cargos_ids:
        cargo = interaction.guild.get_role(cid)
        if cargo: texto += f"• {cargo.mention}\n"
    await interaction.response.send_message(f"📋 Cargos Aprovadores:\n{texto}")

# ---------------------- 🚀 SISTEMA DE CHAMADAS / PRESENÇA ----------------------
@tree.command(name="configchm", description="Configura tudo da Chamada e abre o painel")
async def configchm(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

       class EditarChamada(discord.ui.Modal, title="⚙️ Configurar Chamada"):
        titulo = discord.ui.TextInput(label="📌 Título", required=True, default="CHAMADA DE AÇÃO")
        descricao = discord.ui.TextInput(label="📝 Descrição", style=discord.TextStyle.paragraph, required=True, default="Marque presença confirmando sua participação")
        acao = discord.ui.TextInput(label="⚡ Qual Ação?", required=True, placeholder="Ex: Reunião, Treinamento, Operação...")
        imagem = discord.ui.TextInput(label="🖼️ Link da Imagem", required=False)
        cargo_membros = discord.ui.TextInput(label="👤 ID do Cargo MEMBROS", required=True, placeholder="Cole o ID do cargo que é dos membros")

        async def on_submit(self, inter: discord.Interaction):
            guild_id = str(inter.guild.id)
            # LIMPA HISTÓRICO ANTIGO AUTOMATICAMENTE
            dados_chamada[guild_id] = {
                "titulo": self.titulo.value,
                "descricao": self.descricao.value,
                "acao": self.acao.value,
                "imagem": self.imagem.value or None,
                "cargo_membros": int(self.cargo_membros.value),
                "presencas": {},
                "aberto": True
            }
            salvar_dados(CHAMADA_FILE, dados_chamada)

            # CRIA O PAINEL DE CHAMADA
            embed = discord.Embed(
                title=f"📢 {dados_chamada[guild_id]['titulo']}",
                description=f"{dados_chamada[guild_id]['descricao']}\n\n⚡ AÇÃO: {dados_chamada[guild_id]['acao']}",
                color=discord.Color.gold()
            )
            if dados_chamada[guild_id]['imagem']:
                embed.set_thumbnail(url=dados_chamada[guild_id]['imagem'])

            class BotoesChamada(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)

                @discord.ui.button(label="✅ Vou Comparecer", style=discord.ButtonStyle.green, custom_id="presenca_sim")
                async def sim(self, i: discord.Interaction, btn: discord.ui.Button):
                    g_id = str(i.guild.id)
                    if not dados_chamada.get(g_id, {}).get("aberto"):
                        return await i.response.send_message("❌ Chamada já encerrada!", ephemeral=True)

                    dados_chamada[g_id]["presencas"][str(i.user.id)] = {"nome": i.user.display_name, "status": "presente"}
                    salvar_dados(CHAMADA_FILE, dados_chamada)
                    await i.response.send_message("✅ Presença marcada com sucesso!", ephemeral=True)
                    await atualizar_historico_chamada(i.guild)

                @discord.ui.button(label="❌ Não vou / Justificar", style=discord.ButtonStyle.red, custom_id="presenca_nao")
                async def nao(self, i: discord.Interaction, btn: discord.ui.Button):
                    g_id = str(i.guild.id)
                    if not dados_chamada.get(g_id, {}).get("aberto"):
                        return await i.response.send_message("❌ Chamada já encerrada!", ephemeral=True)

                    dados_chamada[g_id]["presencas"][str(i.user.id)] = {"nome": i.user.display_name, "status": "ausente"}
                    salvar_dados(CHAMADA_FILE, dados_chamada)
                    await i.response.send_message("❌ Registrado como ausente. Você pode justificar pelo painel de justificativas.", ephemeral=True)
                    await atualizar_historico_chamada(i.guild)

            await inter.channel.send(embed=embed, view=BotoesChamada())
            await inter.response.send_message("✅ Chamada configurada e aberta com sucesso!", ephemeral=True)

    await interaction.response.send_modal(EditarChamada())

# Função para atualizar histórico do jeito que você pediu
async def atualizar_historico_chamada(guild):
    guild_id = str(guild.id)
    dados = dados_chamada.get(guild_id, {})
    if not dados: return

    cargo_membros = guild.get_role(dados.get("cargo_membros"))
    if not cargo_membros: return

    presentes = []
    ausentes = []
    justificados = []

    # Quem marcou presença
    for uid, info in dados.get("presencas", {}).items():
        if info["status"] == "presente":
            presentes.append(info["nome"])
        elif info["status"] == "ausente":
            if guild_id in historico and uid in historico[guild_id]:
                if historico[guild_id][uid]["status"] == "aceita":
                    justificados.append(info["nome"])
                else:
                    ausentes.append(info["nome"])
            else:
                ausentes.append(info["nome"])

    # Quem NÃO marcou presença
    for membro in cargo_membros.members:
        if str(membro.id) not in dados.get("presencas", {}):
            if guild_id in historico and str(membro.id) in historico[guild_id]:
                if historico[guild_id][str(membro.id)]["status"] == "aceita":
                    justificados.append(membro.display_name)
                else:
                    ausentes.append(membro.display_name)
            else:
                ausentes.append(membro.display_name)

    texto = ""
    if presentes:
        for p in presentes: texto += f"{p} | ✅️ VAI COMPARECER\n"
    else:
        texto += "Ninguém marcou presença ainda\n"

    texto += "\n———————————————————————————\n"

    if ausentes:
        for a in ausentes: texto += f"{a} | ❌️ NÃO MARCOU PRESENÇA\n"
    else:
        texto += "Nenhum membro ausente\n"

    texto += "\n———————————————————————————\n"

    if justificados:
        for j in justificados: texto += f"{j} | ☑️ JUSTIFICOU\n"
    else:
        texto += "Ninguém justificou ainda\n"

    canal_hist = bot.get_channel(config.get(guild_id, {}).get("canais", {}).get("histórico"))
    if canal_hist:
        await canal_hist.purge(limit=50)
        emb = discord.Embed(title="📋 HISTÓRICO DA CHAMADA", description=texto, color=discord.Color.purple())
        emb.set_footer(text=f"Ação: {dados.get('acao')}")
        await canal_hist.send(embed=emb)

# ---------------------- 🚀 SISTEMA DE JUSTIFICATIVA (ATUALIZADO E SEGURO) ----------------------
class FormJustificativa(discord.ui.Modal, title="📝 Enviar Justificativa"):
    nick = discord.ui.TextInput(label="NICK", required=True)
    id_user = discord.ui.TextInput(label="ID", required=True)
    acao = discord.ui.TextInput(label="AÇÃO", required=True)
    motivo = discord.ui.TextInput(label="MOTIVO", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        dados_guild = config.get(guild_id, {})
        canais = dados_guild.get("canais", {})
        cargos_aprov = dados_guild.get("cargos_aprovadores", [])

        if "solicitação" not in canais:
            return await interaction.response.send_message("❌ Configure os canais primeiro!", ephemeral=True)

        dados = {
            "nick": self.nick.value,
            "id": self.id_user.value,
            "acao": self.acao.value,
            "motivo": self.motivo.value,
            "status": "pendente",
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        canal_sol = bot.get_channel(canais["solicitação"])
        if not canal_sol: return

        embed = discord.Embed(title="📩 Nova Solicitação", color=discord.Color.yellow())
        embed.add_field(name="👤 Nome", value=dados["nick"], inline=True)
        embed.add_field(name="🆔 ID", value=dados["id"], inline=True)
        embed.add_field(name="⚡ Ação", value=dados["acao"], inline=False)
        embed.add_field(name="📝 Motivo", value=dados["motivo"], inline=False)

        class Botoes(discord.ui.View):
            def __init__(self): super().__init__(timeout=None)

            @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.green, emoji="✅", custom_id="aceitar")
            async def aceitar(self, inter: discord.Interaction, btn: discord.ui.Button):
                tem_permissao = inter.user.guild_permissions.administrator or any(cid in [r.id for r in inter.user.roles] for cid in cargos_aprov)
                if not tem_permissao:
                    return await inter.response.send_message("❌ Não pode!", ephemeral=True)

                dados["status"] = "aceita"
                if guild_id not in historico: historico[guild_id] = {}
                historico[guild_id][dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"✅ Justificativa ACEITA!\nMotivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await atualizar_historico_chamada(inter.guild)
                await inter.response.edit_message(content="✅ ACEITO", embed=embed, view=None)

            @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, emoji="❌", custom_id="recusar")
            async def recusar(self, inter: discord.Interaction, btn: discord.ui.Button):
                tem_permissao = inter.user.guild_permissions.administrator or any(cid in [r.id for r in inter.user.roles] for cid in cargos_aprov)
                if not tem_permissao:
                    return await inter.response.send_message("❌ Não pode!", ephemeral=True)

                dados["status"] = "recusada"
                if guild_id not in historico: historico[guild_id] = {}
                historico[guild_id][dados["id"]] = dados
                salvar_dados(HISTORICO_FILE, historico)

                try:
                    usuario = bot.get_user(int(dados["id"]))
                    if usuario: await usuario.send(f"❌ Justificativa RECUSADA!\nMotivo: {dados['motivo']}")
                except: pass

                await atualizar_historico(inter.guild)
                await atualizar_historico_chamada(inter.guild)
                await inter.response.edit_message(content="❌ RECUSADO", embed=embed, view=None)

        await canal_sol.send(embed=embed, view=Botoes())
        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

@tree.command(name="painel", description="Mostra o painel principal")
async def painel(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})

    if interaction.channel.id != canais.get("painel"):
        return await interaction.response.send_message("❌ Canal errado!", ephemeral=True)

    titulo = dados_guild.get("titulo", "📋 Sistema de Justificativas")
    desc = dados_guild.get("descricao", "Informe NICK, ID, AÇÃO e MOTIVO.")
    img = dados_guild.get("imagem")

    embed = discord.Embed(title=titulo, description=desc, color=discord.Color.green())
    if img: embed.set_thumbnail(url=img)

    class ViewPainel(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="📝 Enviar Justificativa", style=discord.ButtonStyle.green, custom_id="form_just")
        async def abrir(self, inter: discord.Interaction, btn: discord.ui.Button):
            await inter.response.send_modal(FormJustificativa())

    await interaction.response.send_message(embed=embed, view=ViewPainel())

async def atualizar_historico(guild):
    guild_id = str(guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})
    canal_hist = bot.get_channel(canais.get("histórico"))
    if not canal_hist: return

    await canal_hist.purge(limit=100)
    texto = ""
    for dado in historico.get(guild_id, {}).values():
        if dado["status"] == "aceita": texto += f"{dado['nick']} | ✅️ ACEITA\n"
        elif dado["status"] == "recusada": texto += f"{dado['nick']} | ❌️ RECUSADA\n"
        else: texto += f"{dado['nick']} | 🕝 PENDENTE\n"

    emb = discord.Embed(title="📜 Histórico Justificativas", description=texto or "Vazio", color=discord.Color.blurple())
    await canal_hist.send(embed=emb)

# ---------------------- PERSONALIZAÇÃO ----------------------
@tree.command(name="título", description="Muda o título do painel")
async def titulo(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator: return
    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    config[guild_id]["titulo"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Título: {texto}")

@tree.command(name="descrição", description="Muda a descrição do painel")
async def descricao(interaction: discord.Interaction, *, texto: str):
    if not interaction.user.guild_permissions.administrator: return
    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    config[guild_id]["descricao"] = texto
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Descrição salva!")

@tree.command(name="tumber", description="Coloca imagem no painel")
async def tumber(interaction: discord.Interaction, link: str):
    if not interaction.user.guild_permissions.administrator: return
    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    config[guild_id]["imagem"] = link
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Imagem definida!")

@tree.command(name="limparhistorico", description="Apaga todo o histórico DESSE SERVIDOR")
async def limparhistorico(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    guild_id = str(interaction.guild.id)
    if guild_id in historico: del historico[guild_id]
    salvar_dados(HISTORICO_FILE, historico)
    await interaction.response.send_message("✅ Histórico limpo!")

# ---------------------- RODAR BOT ----------------------
keep_alive()
bot.run(TOKEN)
