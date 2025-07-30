from django.contrib import admin
# O '.' significa "da aplicação atual"
from .models import Organizacao, Administrador, Usuario, Safra, Interacao, Prompt, State, ProdutoEstoque

# O comando admin.site.register() diz ao Django: "Crie uma interface de CRUD para este modelo"
admin.site.register(Organizacao)
admin.site.register(Administrador)
admin.site.register(Usuario)
admin.site.register(Safra)
admin.site.register(Interacao)
admin.site.register(Prompt)
admin.site.register(State)
admin.site.register(ProdutoEstoque)

# Register your models here.