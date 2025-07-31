from django.db import migrations

def criar_organizacao_padrao(apps, schema_editor):
    """
    Esta função será executada quando aplicarmos a migração.
    Ela cria uma organização padrão na base de dados.
    """
    # Obtemos o modelo 'Organizacao' para esta versão da migração
    Organizacao = apps.get_model('chatbot', 'Organizacao')
    # Criamos uma instância com ID=1 e nome 'Organização Padrão'
    Organizacao.objects.create(
        id=1,
        nome='Organização Padrão'
    )

def remover_organizacao_padrao(apps, schema_editor):
    """
    Esta função é executada se precisarmos de reverter a migração.
    Ela apaga a organização que criámos.
    """
    Organizacao = apps.get_model('chatbot', 'Organizacao')
    Organizacao.objects.filter(id=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        # Esta migração depende da primeira, que criou as tabelas.
        ('chatbot', '0001_initial'),
    ]

    operations = [
        # Dizemos ao Django para executar a nossa função personalizada.
        migrations.RunPython(criar_organizacao_padrao, reverse_code=remover_organizacao_padrao),
    ]
