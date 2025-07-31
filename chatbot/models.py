# chatbot/models.py
from django.db import models
from django.contrib.auth.models import User

# =======================
# TABELA DE ORGANIZAÇÕES
# =======================
class Organizacao(models.Model):
    nome = models.CharField(max_length=255, unique=True, null=False)
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"
        db_table = 'tb_organizacoes'

# =========================
# TABELA DE ADMINISTRADORES
# =========================
class Administrador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='administrador_profile', null=True, blank=True)
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE, related_name='administradores')
    nome = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, unique=True, null=False)
    cargo = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        db_table = 'tb_administradores'

# ========================
# TABELA DE USUÁRIOS (AGRICULTORES)
# ========================
class Usuario(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Ativo', # Define 'Ativo' como o padrão para novos usuários
        verbose_name="Status do Usuário"
    )
    
    organizacao = models.ForeignKey(Organizacao, on_delete=models.CASCADE, related_name='usuarios')
    nome = models.CharField(max_length=255)
    whatsapp_id = models.CharField(max_length=50, unique=True, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_atividade = models.DateTimeField(null=True, blank=True)
    contexto = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.whatsapp_id})"

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        db_table = 'tb_usuarios'

# ================
# TABELA DE SAFRAS
# ================
class Safra(models.Model):
    agricultor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='safras')
    cultura = models.CharField(max_length=255)
    ano_safra = models.CharField(max_length=10, null=True, blank=True)
    area_plantada_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    produtividade = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unidade_medida = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.cultura} - {self.agricultor.nome}"

    class Meta:
        verbose_name = "Safra"
        verbose_name_plural = "Safras"
        db_table = 'tb_safras'

# ============================
# TABELA DE PRODUTOS EM ESTOQUE
# ============================
class ProdutoEstoque(models.Model):
    agricultor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='produtos_estoque')
    nome = models.CharField(max_length=255)
    tipo_produto = models.CharField(max_length=50)
    unidade_medida = models.CharField(max_length=20)
    saldo_atual = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Produto em Estoque"
        verbose_name_plural = "Produtos em Estoque"
        db_table = 'tb_produtos_estoque'

# ========================
# TABELA DE INTERAÇÕES
# ========================
class Interacao(models.Model):
    agricultor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='interacoes')
    mensagem_usuario = models.TextField(null=True, blank=True)
    resposta_chatbot = models.TextField(null=True, blank=True)
    entidades = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interação com {self.agricultor.nome} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Interação"
        verbose_name_plural = "Interações"
        db_table = 'tb_interacoes'

# ==================================
# NOVA TABELA DE PROMPTS DO CHATBOT
# ==================================
class Prompt(models.Model):
    """
    Armazena os textos (prompts) utilizados pelo chatbot.
    """
    key = models.CharField(
        max_length=100, 
        primary_key=True, 
        help_text="Chave única para identificar o prompt no código (ex: 'welcome_message')"
    )
    text = models.TextField(
        help_text="O texto que será enviado para o usuário. Pode conter {placeholders}."
    )
    description = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Descrição interna para explicar onde este prompt é usado."
    )

    def __str__(self):
        return self.key
        
    class Meta:
        verbose_name = "Prompt do Chatbot"
        verbose_name_plural = "Prompts do Chatbot"
        db_table = 'tb_prompts'
        
class State(models.Model):
    """
    Armazena os estados brasileiros e suas siglas.
    """
    abbreviation = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"
        db_table = 'tb_states'