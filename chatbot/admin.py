from django.contrib import admin
from .models import (
    Organizacao, Administrador, Usuario, Safra, Interacao, 
    Prompt, State, ProdutoEstoque
)

@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'cnpj', 'data_criacao')
    search_fields = ('nome', 'cnpj')

@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cargo', 'organizacao')
    list_filter = ('organizacao', 'cargo')
    search_fields = ('nome', 'email')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # 1. Esta linha aponta para o seu ficheiro HTML customizado.
    change_list_template = "admin/chatbot/usuario/painel_usuarios_custom.html"

    # Estas configurações são para a lista padrão, mas é bom mantê-las.
    list_display = ('nome', 'whatsapp_id', 'cidade', 'estado', 'organizacao', 'status')
    list_filter = ('organizacao', 'estado', 'status')
    search_fields = ('nome', 'whatsapp_id', 'cidade')

    def changelist_view(self, request, extra_context=None):
        # 2. Esta função calcula e adiciona os seus dados customizados à página.
        
        # Obtém a lista de usuários, já filtrada pela organização do admin logado.
        queryset = self.get_queryset(request)

        # Aplica o filtro de busca da sua caixa de pesquisa customizada.
        filtro_cidade = request.GET.get('localizacao', '')
        if filtro_cidade:
            queryset = queryset.filter(cidade__icontains=filtro_cidade)

        # Calcula os totais.
        ativos = queryset.filter(status='Ativo').count()
        inativos = queryset.filter(status='Inativo').count()

        # Passa todos os dados para o seu template.
        extra_context = extra_context or {}
        extra_context['usuarios'] = queryset  # O seu template usa a variável 'usuarios'
        extra_context['total'] = queryset.count()
        extra_context['ativos'] = ativos
        extra_context['inativos'] = inativos
        
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Filtra a lista de usuários para mostrar apenas os da organização do admin."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs # Superusuário vê tudo
        try:
            admin_profile = request.user.administrador_profile
            return qs.filter(organizacao=admin_profile.organizacao)
        except Administrador.DoesNotExist:
            return qs.none()

    def has_change_permission(self, request, obj=None):
        """Permite que um admin edite APENAS usuários da sua organização."""
        if request.user.is_superuser:
            return True
        if obj is not None:
            try:
                admin_profile = request.user.administrador_profile
                return obj.organizacao == admin_profile.organizacao
            except Administrador.DoesNotExist:
                return False
        return hasattr(request.user, 'administrador_profile')

    def has_delete_permission(self, request, obj=None):
        """Permite que um admin apague APENAS usuários da sua organização."""
        # Reutiliza a mesma lógica da permissão de edição
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        """Permite que um admin adicione novos usuários (que serão automaticamente da sua organização)."""
        return request.user.is_superuser or hasattr(request.user, 'administrador_profile')

    def save_model(self, request, obj, form, change):
        """Ao criar um novo usuário, define a organização automaticamente."""
        if not change and not request.user.is_superuser: # Se está a adicionar e não é superuser
            try:
                admin_profile = request.user.administrador_profile
                obj.organizacao = admin_profile.organizacao
            except Administrador.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)
    
@admin.register(Safra)
class SafraAdmin(admin.ModelAdmin):
    list_display = ('cultura', 'agricultor', 'ano_safra', 'area_plantada_ha')
    list_filter = ('cultura', 'ano_safra', 'agricultor__organizacao')
    search_fields = ('cultura', 'agricultor__nome')

@admin.register(ProdutoEstoque)
class ProdutoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_produto', 'saldo_atual', 'unidade_medida', 'agricultor')
    list_filter = ('tipo_produto', 'agricultor__organizacao')
    search_fields = ('nome', 'agricultor__nome')

@admin.register(Interacao)
class InteracaoAdmin(admin.ModelAdmin):
    list_display = ('agricultor', 'timestamp', 'mensagem_usuario', 'resposta_chatbot')
    list_filter = ('timestamp', 'agricultor__organizacao')
    search_fields = ('mensagem_usuario', 'resposta_chatbot', 'agricultor__nome')

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'text')
    search_fields = ('key', 'text')

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('abbreviation', 'name')
    search_fields = ('name',)