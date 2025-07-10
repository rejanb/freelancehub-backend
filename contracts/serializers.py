from rest_framework import serializers
from .models import Contract
from proposals.models import Proposal
from proposals.serializers import ProposalSerializer  # Assumes you have this

class ContractSerializer(serializers.ModelSerializer):
    proposal = ProposalSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'