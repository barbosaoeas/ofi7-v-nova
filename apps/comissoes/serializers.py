from rest_framework import serializers

from .models import Comissao


class ComissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comissao
        fields = [
            'id',
            'funcionario',
            'ordem',
            'etapa',
            'aprovado_por',
            'valor_servico',
            'percentual',
            'valor',
            'tempo_execucao_horas',
            'status_pagamento',
            'data_execucao',
            'data_aprovacao',
            'data_pagamento',
            'observacao',
            'criado_em',
            'atualizado_em',
        ]


class AprovarComissaoSerializer(serializers.Serializer):
    aprovado_por = serializers.IntegerField(required=False)


class MarcarComoPagaSerializer(serializers.Serializer):
    pago = serializers.BooleanField(required=False, default=True)
