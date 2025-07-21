import discord
from discord.ext import commands
from discord.utils import get

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Catálogo de produtos
produtos = {
    "botg": {"nome": "Bot Geral", "preco": "R$ 40,00", "descricao": "Bot completo que faz tudo"},
    "bott": {"nome": "Bot de Ticket", "preco": "R$ 30,00", "descricao": "Bot de tickets para suporte"},
    "botm": {"nome": "Bot de Música", "preco": "R$ 30,00", "descricao": "Bot de música com várias funções"},
}

# Configurações
SUPORTE_ROLE = "Suporte"
CARGO_COMPRADOR = "Comprador"
CATEGORIA_TICKET = "Tickets"
CANAL_LOG = "pedidos-log"

class ConfirmarPagamentoView(discord.ui.View):
    def __init__(self, comprador, produto_id):
        super().__init__(timeout=None)
        self.comprador = comprador
        self.produto_id = produto_id

    @discord.ui.button(label="✅ Confirmar pagamento", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not get(interaction.user.roles, name=SUPORTE_ROLE):
            return await interaction.response.send_message("Apenas o suporte pode confirmar.", ephemeral=True)

        role = get(interaction.guild.roles, name=CARGO_COMPRADOR)
        if role:
            await self.comprador.add_roles(role)

        await interaction.channel.send(f"✅ Pagamento confirmado para {self.comprador.mention}. Cargo atribuído!")

        log = get(interaction.guild.text_channels, name=CANAL_LOG)
        if log:
            await log.send(f"📦 Produto: **{produtos[self.produto_id]['nome']}** entregue para {self.comprador.mention}")

        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self, user, produto_id):
        super().__init__(timeout=None)
        self.user = user
        self.produto_id = produto_id

    @discord.ui.button(label="✅ Já paguei", style=discord.ButtonStyle.blurple)
    async def criar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Somente o comprador pode clicar aqui.", ephemeral=True)

        guild = interaction.guild
        categoria = get(guild.categories, name=CATEGORIA_TICKET)
        if not categoria:
            categoria = await guild.create_category(CATEGORIA_TICKET)

        canal_nome = f"ticket-{self.user.name.lower()}"
        existente = get(guild.text_channels, name=canal_nome)
        if existente:
            return await interaction.response.send_message(f"Você já tem um ticket aberto: {existente.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True),
        }

        suporte = get(guild.roles, name=SUPORTE_ROLE)
        if suporte:
            overwrites[suporte] = discord.PermissionOverwrite(view_channel=True)

        canal = await guild.create_text_channel(canal_nome, category=categoria, overwrites=overwrites)
        await canal.send(
            f"{self.user.mention}, seu pedido de **{produtos[self.produto_id]['nome']}** está em análise.\n"
            f"A equipe de suporte confirmará o pagamento em breve.",
            view=ConfirmarPagamentoView(self.user, self.produto_id)
        )

        await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

@bot.tree.command(name="produtos", description="Veja os produtos disponíveis")
async def slash_produtos(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 Catálogo de Produtos", color=0x00ff00)
    for pid, p in produtos.items():
        embed.add_field(
            name=f"{p['nome']} — {p['preco']}",
            value=f"{p['descricao']}\nUse `/comprar {pid}` para adquirir.",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="comprar", description="Comprar um produto do catálogo")
async def slash_comprar(interaction: discord.Interaction, produto: str):
    produto = produto.lower()
    if produto not in produtos:
        return await interaction.response.send_message("❌ Produto inválido. Use `/produtos` para ver a lista.", ephemeral=True)

    p = produtos[produto]
    embed = discord.Embed(
        title=f"💳 Compra de {p['nome']}",
        description=(
            f"💰 Valor: {p['preco']}\n"
            f"{p['descricao']}\n\n"
            "Após pagamento no Pix `adrianalmarques80@gmail.com`, clique no botão abaixo."
        ),
        color=0x3498db
    )

    await interaction.response.send_message(embed=embed, view=TicketView(interaction.user, produto), ephemeral=True)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands sincronizados: {len(synced)} comandos")
    except Exception as e:
        print(f"Erro ao registrar slash commands: {e}")
    print(f"🤖 Bot online como {bot.user}")

bot.run("MTM5NjgyNDc4NzUwMTk3MzYxNA.Gzl5BO.Sx7grDNe9PfsqUI-8odWoQwTAjabhfqdCgMDiE")
