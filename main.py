import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import asyncio
import os
import base64
from keep_alive import keep_alive

# ---------------------- 🛡️ SEGURANÇA TOTAL 🛡️ ----------------------
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("🔴 TOKEN NÃO ENCONTRADO! BOT PARADO POR SEGURANÇA.")
    exit()

# Nomes de arquivos ocultos e criptografados
CONFIG_FILE = ".cfg_secure_9f2d.json"
HISTORICO_FILE = ".hist_secure_7x4a.json"
CHAMADA_FILE = ".cham_secure_3z8b.json"

# Intents básicos
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# ---------------------- 🔐 SISTEMA DE CRIPTOGRAFIA ----------------------
def codificar_dados(dados):
    texto_json = json.dumps(dados, indent=4, ensure_ascii=False)
    return base64.b64encode(texto_json.encode('utf-8')).decode('utf-8')

def decodificar_dados(texto_codificado):
    try:
        texto_json = base64.b64decode(texto_codificado.encode('utf-8')).decode('utf-8')
        return json.loads(texto_json)
    except:
        return {}

# ---------------------- 📂 FUNÇÕES DE CARREGAR/SALVAR ----------------------
def carregar_dados(arquivo):
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            return decodificar_dados(conteudo)
    except:
        return {}

def salvar_dados(arquivo, dados):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(codificar_dados(dados))
    except Exception as e:
        print(f"Erro ao salvar: {e}")

# Carrega dados
config = carregar_dados(CONFIG_FILE)
historico = carregar_dados(HISTORICO_FILE)
dados_chamada = carregar_dados(CHAMADA_FILE)

# ---------------------- ✅ MANTER ONLINE ----------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ONLINE como: {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔄 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro: {e}")

# ---------------------- 🚀 CONFIGURAR CANAIS ----------------------
@tree.command(name="configcanal", description="Define os canais do sistema")
@app_commands.describe(tipo="Escolha", canal="ID ou Menção")
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
            return await interaction.response.send_message("❌ Canal não encontrado!", ephemeral=True)
    except:
        return await interaction.response.send_message("❌ ID inválido!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    if "canais" not in config[guild_id]: config[guild_id]["canais"] = {}

    config[guild_id]["canais"][tipo.value] = canal_obj.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal de {tipo.name}: {canal_obj.mention}", ephemeral=True)

# ---------------------- 🚀 HISTÓRICO DE CHAMADAS ----------------------
@tree.command(name="historicocmh", description="Define canal onde aparecerá o histórico de chamadas")
async def historicocmh(interaction: discord.Interaction, canal: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    try:
        canal_id = int(canal.strip("<>#"))
        canal_obj = bot.get_channel(canal_id)
        if not canal_obj:
            return await interaction.response.send_message("❌ Canal não encontrado!", ephemeral=True)
    except:
        return await interaction.response.send_message("❌ ID inválido!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    if guild_id not in config: config[guild_id] = {}
    if "canais" not in config[guild_id]: config[guild_id]["canais"] = {}

    config[guild_id]["canais"]["historico_chamada"] = canal_obj.id
    salvar_dados(CONFIG_FILE, config)
    await interaction.response.send_message(f"✅ Canal Histórico de Chamadas: {canal_obj.mention}", ephemeral=True)

# ---------------------- 🚀 CARGOS APROVADORES ----------------------
@tree.command(name="addcargoaprovador", description="Adiciona cargo que aprova justificativas")
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
        await interaction.response.send_message(f"✅ Cargo {cargo.mention} adicionado!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Já existe!", ephemeral=True)

@tree.command(name="listacargosaprovadores", description="Lista cargos aprovadores")
async def listacargosaprovadores(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    cargos_ids = config.get(guild_id, {}).get("cargos_aprovadores", [])
    if not cargos_ids:
        return await interaction.response.send_message("❌ Nenhum cargo cadastrado!", ephemeral=True)

    texto = ""
    for cid in cargos_ids:
        cargo = interaction.guild.get_role(cid)
        if cargo: texto += f"• {cargo.mention}\n"
    await interaction.response.send_message(f"📋 Cargos:\n{texto}", ephemeral=True)

# ---------------------- 🚀 CONFIG PAINEL (EDIÇÃO COMPLETA) ----------------------
@tree.command(name="configpainel", description="Edita Título, Descrição, Botão, Rodapé e Imagem do painel")
async def configpainel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    class EditarPainel(discord.ui.Modal, title="⚙️ Editar Painel de Justificativas"):
        titulo = discord.ui.TextInput(
            label="📌 Título do Painel",
            required=True,
            default=config.get(str(interaction.guild.id), {}).get("titulo", "📋 Sistema de Justificativas")
        )
        descricao = discord.ui.TextInput(
            label="📝 Descrição",
            style=discord.TextStyle.paragraph,
            required=True,
            default=config.get(str(interaction.guild.id), {}).get("descricao", "Informe NICK, ID, AÇÃO e MOTIVO.")
        )
        texto_botao = discord.ui.TextInput(
            label="🔘 Texto do Botão",
            required=True,
            default=config.get(str(interaction.guild.id), {}).get("texto_botao", "📝 Enviar Justificativa")
        )
        rodape = discord.ui.TextInput(
            label="📌 Rodapé / Texto final",
            required=False,
            default=config.get(str(interaction.guild.id), {}).get("rodape", "Sistema automático de justificativas")
        )
        imagem = discord.ui.TextInput(
            label="🖼️ Link da Imagem",
            required=False,
            default=config.get(str(interaction.guild.id), {}).get("imagem", "")
        )

        async def on_submit(self, inter: discord.Interaction):
            guild_id = str(inter.guild.id)
            if guild_id not in config: config[guild_id] = {}

            config[guild_id]["titulo"] = self.titulo.value
            config[guild_id]["descricao"] = self.descricao.value
            config[guild_id]["texto_botao"] = self.texto_botao.value
            config[guild_id]["rodape"] = self.rodape.value
            config[guild_id]["imagem"] = self.imagem.value or None

            salvar_dados(CONFIG_FILE, config)
            await inter.response.send_message("✅ Painel atualizado com sucesso!", ephemeral=True)

    await interaction.response.send_modal(EditarPainel())

# ---------------------- 🚀 SISTEMA DE CHAMADAS /PAINELCMH ----------------------
@tree.command(name="painelcmh", description="Abre e configura o painel de chamadas")
async def painelcmh(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    class EditarChamada(discord.ui.Modal, title="⚙️ Configurar Chamada"):
        titulo = discord.ui.TextInput(label="📌 Título", required=True, default="CHAMADA DE AÇÃO")
        descricao = discord.ui.TextInput(label="📝 Descrição", style=discord.TextStyle.paragraph, required=True, default="Marque presença confirmando sua participação")
        acao = discord.ui.TextInput(label="⚡ Qual Ação?", required=True, placeholder="Ex: Reunião, Treinamento")
        imagem = discord.ui.TextInput(label="🖼️ Link Imagem", required=False)
        cargo_membros = discord.ui.TextInput(label="👤 ID Cargo MEMBROS", required=True)

        async def on_submit(self, inter: discord.Interaction):
            guild_id = str(inter.guild.id)
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
                        return await i.response.send_message("❌ Encerrada!", ephemeral=True)

                    dados_chamada[g_id]["presencas"][str(i.user.id)] = {"nome": i.user.display_name, "status": "presente"}
                    salvar_dados(CHAMADA_FILE, dados_chamada)
                    await i.response.send_message("✅ Presença confirmada!", ephemeral=True)
                    await atualizar_historico_chamada(i.guild)

                @discord.ui.button(label="❌ Não vou / Justificar", style=discord.ButtonStyle.red, custom_id="presenca_nao")
                async def nao(self, i: discord.Interaction, btn: discord.ui.Button):
                    g_id = str(i.guild.id)
                    if not dados_chamada.get(g_id, {}).get("aberto"):
                        return await i.response.send_message("❌ Encerrada!", ephemeral=True)

                    dados_chamada[g_id]["presencas"][str(i.user.id)] = {"nome": i.user.display_name, "status": "ausente"}
                    salvar_dados(CHAMADA_FILE, dados_chamada)
                    await i.response.send_message("❌ Registrado como ausente.", ephemeral=True)
                    await atualizar_historico_chamada(i.guild)

            await inter.channel.send(embed=embed, view=BotoesChamada())
            await inter.response.send_message("✅ Painel de Chamadas aberto!", ephemeral=True)

    await interaction.response.send_modal(EditarChamada())

# ---------------------- 🔄 ATUALIZAR HISTÓRICO CHAMADA (EMBED BONITO) ----------------------
async def atualizar_historico_chamada(guild):
    guild_id = str(guild.id)
    dados = dados_chamada.get(guild_id, {})
    if not dados: return

    cargo_membros = guild.get_role(dados.get("cargo_membros"))
    if not cargo_membros: return

    presentes = []
    ausentes = []
    justificados = []

    for uid, info in dados.get("presencas", {}).items():
        if info["status"] == "presente":
            presentes.append(f"✅ {info['nome']}")
        elif info["status"] == "ausente":
            if guild_id in historico and uid in historico[guild_id]:
                if historico[guild_id][uid]["status"] == "aceita":
                    justificados.append(f"☑️ {info['nome']}")
                else:
                    ausentes.append(f"❌ {info['nome']}")
            else:
                ausentes.append(f"❌ {info['nome']}")

    for membro in cargo_membros.members:
        if str(membro.id) not in dados.get("presencas", {}):
            if guild_id in historico and str(membro.id) in historico[guild_id]:
                if historico[guild_id][str(membro.id)]["status"] == "aceita":
                    justificados.append(f"☑️ {membro.display_name}")
                else:
                    ausentes.append(f"❌ {membro.display_name}")
            else:
                ausentes.append(f"❌ {membro.display_name}")

    # 🎨 VISUAL NOVO E ORGANIZADO
    embed = discord.Embed(
        title="📋 HISTÓRICO DA CHAMADA",
        description=f"**Ação:** {dados.get('acao')}\n**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        color=discord.Color.purple()
    )

    embed.add_field(name="✅ PRESENTES", value="\n".join(presentes) if presentes else "Ninguém marcou presença", inline=False)
    embed.add_field(name="❌ AUSENTES", value="\n".join(ausentes) if ausentes else "Nenhum ausente", inline=False)
    embed.add_field(name="☑️ JUSTIFICADOS", value="\n".join(justificados) if justificados else "Ninguém justificou", inline=False)

    canal_hist = bot.get_channel(config.get(guild_id, {}).get("canais", {}).get("historico_chamada"))
    if canal_hist:
        await canal_hist.purge(limit=50)
        await canal_hist.send(embed=embed)

# ---------------------- 🚀 SISTEMA DE JUSTIFICATIVA ----------------------
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
            return await interaction.response.send_message("❌ Configure canais primeiro!", ephemeral=True)

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
                    return await inter.response.send_message("❌ Sem permissão!", ephemeral=True)

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
                    return await inter.response.send_message("❌ Sem permissão!", ephemeral=True)

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

# ---------------------- 🚀 PAINEL PRINCIPAL ----------------------
@tree.command(name="painel", description="Mostra painel de justificativas")
async def painel(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})

    if interaction.channel.id != canais.get("painel"):
        return await interaction.response.send_message("❌ Canal errado!", ephemeral=True)

    titulo = dados_guild.get("titulo", "📋 Sistema de Justificativas")
    desc = dados_guild.get("descricao", "Informe NICK, ID, AÇÃO e MOTIVO.")
    texto_botao = dados_guild.get("texto_botao", "📝 Enviar Justificativa")
    rodape = dados_guild.get("rodape", "")
    img = dados_guild.get("imagem")

    embed = discord.Embed(title=titulo, description=desc, color=discord.Color.green())
    if img: embed.set_thumbnail(url=img)
    if rodape: embed.set_footer(text=rodape)

    class ViewPainel(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label=texto_botao, style=discord.ButtonStyle.green, custom_id="form_just")
        async def abrir(self, inter: discord.Interaction, btn: discord.ui.Button):
            await inter.response.send_modal(FormJustificativa())

    await interaction.response.send_message(embed=embed, view=ViewPainel())

# ---------------------- 🔄 ATUALIZAR HISTÓRICO JUSTIFICATIVAS ----------------------
async def atualizar_historico(guild):
    guild_id = str(guild.id)
    dados_guild = config.get(guild_id, {})
    canais = dados_guild.get("canais", {})
    canal_hist = bot.get_channel(canais.get("histórico"))
    if not canal_hist: return

    await canal_hist.purge(limit=100)
    texto = ""
    for dado in historico.get(guild_id, {}).values():
        if dado["status"] == "aceita": texto += f"✅ {dado['nick']} | ACEITA\n"
        elif dado["status"] == "recusada": texto += f"❌ {dado['nick']} | RECUSADA\n"
        else: texto += f"🕝 {dado['nick']} | PENDENTE\n"

    emb = discord.Embed(title="📜 Histórico Justificativas", description=texto or "Vazio", color=discord.Color.blurple())
    await canal_hist.send(embed=emb)

# ---------------------- ⚙️ VER CONFIGURAÇÕES GERAIS ----------------------
@tree.command(name="configver", description="Ver todas as configurações separadas")
async def configver(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)

    guild_id = str(interaction.guild.id)
    dados = config.get(guild_id, {})
    canais = dados.get("canais", {})
    cargos = dados.get("cargos_aprovadores", [])

    # 📌 JUSTIFICATIVAS
    embed_just = discord.Embed(title="📌 CONFIGURAÇÕES - JUSTIFICATIVAS", color=discord.Color.green())
    embed_just.add_field(name="Título", value=dados.get("titulo", "Padrão"), inline=False)
    embed_just.add_field(name="Descrição", value=dados.get("descricao", "Padrão"), inline=False)
    embed_just.add_field(name="Texto do Botão", value=dados.get("texto_botao", "Padrão"), inline=False)
    embed_just.add_field(name="Rodapé", value=dados.get("rodape", "Padrão"), inline=False)
    embed_just.add_field(name="Imagem", value=dados.get("imagem", "Nenhuma"), inline=False)
    embed_just.add_field(name="Canal Painel", value=f"<#{canais.get('painel')}>" if canais.get('painel') else "❌ Não definido", inline=True)
    embed_just.add_field(name="Canal Solicitações", value=f"<#{canais.get('solicitação')}>" if canais.get('solicitação') else "❌ Não definido", inline=True)
    embed_just.add_field(name="Canal Histórico", value=f"<#{canais.get('histórico')}>" if canais.get('histórico') else "❌ Não definido", inline=True)

    # 📢 CHAMADAS
    embed_cham = discord.Embed(title="📢 CONFIGURAÇÕES - CHAMADAS", color=discord.Color.gold())
    embed_cham.add_field(name="Canal Histórico Chamada", value=f"<#{canais.get('historico_chamada')}>" if canais.get('historico_chamada') else "❌ Não definido", inline=False)

    # 👤 CARGOS
    texto_cargos = ""
    for cid in cargos:
        cargo = interaction.guild.get_role(cid)
        if cargo: texto_cargos += f"• {cargo.mention}\n"
    if not texto_cargos: texto_cargos = "Nenhum cargo cadastrado"
    embed_cargos = discord.Embed(title="👤 CARGOS APROVADORES", description=texto_cargos, color=discord.Color.orange())

    await interaction.response.send_message(embeds=[embed_just, embed_cham, embed_cargos], ephemeral=True)

# ---------------------- 🚀 LIMPAR HISTÓRICO ----------------------
@tree.command(name="limparhistorico", description="Apaga histórico do servidor")
async def limparhistorico(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    guild_id = str(interaction.guild.id)
    if guild_id in historico: del historico[guild_id]
    salvar_dados(HISTORICO_FILE, historico)
    await interaction.response.send_message("✅ Histórico limpo!", ephemeral=True)

# ---------------------- 🚀 INICIAR BOT ----------------------
keep_alive()
bot.run(TOKEN)
