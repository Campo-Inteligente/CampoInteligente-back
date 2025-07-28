# panel/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from chatbot.models import Organizacao, Administrador

# --- Serializer para Organizações (usado para Criar, Listar e Atualizar) ---

class OrganizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacao
        fields = ['id', 'nome', 'cnpj', 'data_criacao']
        read_only_fields = ['id', 'data_criacao']

    def validate_cnpj(self, value):
        # Na atualização, permite que o CNPJ seja o mesmo do objeto atual
        if self.instance and self.instance.cnpj == value:
            return value
        if Organizacao.objects.filter(cnpj=value).exists():
            raise serializers.ValidationError("Uma organização com este CNPJ já existe.")
        return value

# --- Serializers para Administradores ---

class AdministradorCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    nome = serializers.CharField(required=True, max_length=255)
    cargo = serializers.CharField(required=False, allow_blank=True, max_length=50)
    organizacao_id = serializers.IntegerField(required=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Um usuário com este email já existe.")
        return value

    def validate_organizacao_id(self, value):
        if not Organizacao.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"A organização com ID {value} não foi encontrada.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['nome'].split(' ')[0],
            is_staff=True
        )
        administrador = Administrador.objects.create(
            user=user,
            organizacao_id=validated_data['organizacao_id'],
            nome=validated_data['nome'],
            email=validated_data['email'],
            cargo=validated_data.get('cargo', '')
        )
        return administrador

class AdministradorReadOnlySerializer(serializers.ModelSerializer):
    """Serializer para exibir (GET) os dados de um administrador."""
    organizacao_nome = serializers.CharField(source='organizacao.nome', read_only=True)
    
    class Meta:
        model = Administrador
        fields = ['id', 'nome', 'email', 'cargo', 'organizacao_id', 'organizacao_nome']

# --- NOVO SERIALIZER PARA ATUALIZAÇÃO DE ADMINISTRADOR ---

class AdministradorUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar (PUT/PATCH) um administrador."""
    class Meta:
        model = Administrador
        fields = ['nome', 'email', 'cargo', 'organizacao_id']
        # Todos os campos são opcionais na atualização com PATCH
        extra_kwargs = {
            'nome': {'required': False},
            'email': {'required': False},
            'cargo': {'required': False},
            'organizacao_id': {'required': False},
        }

    def validate_email(self, value):
        # Permite que o email seja o mesmo do objeto atual
        if self.instance and self.instance.email == value:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Um usuário com este email já existe.")
        return value

    def update(self, instance, validated_data):
        # Atualiza o modelo Administrador
        instance.nome = validated_data.get('nome', instance.nome)
        instance.cargo = validated_data.get('cargo', instance.cargo)
        instance.organizacao_id = validated_data.get('organizacao_id', instance.organizacao_id)
        
        # Se o email foi alterado, atualiza também o modelo User
        if 'email' in validated_data:
            new_email = validated_data['email']
            instance.email = new_email
            if instance.user:
                instance.user.email = new_email
                instance.user.username = new_email # Mantém o username sincronizado com o email
                instance.user.save()

        instance.save()
        return instance