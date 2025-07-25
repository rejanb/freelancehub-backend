from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from io import BytesIO
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Count, Sum
from .models import Contract, ContractDocument
from .serializers import ContractSerializer, ContractDocumentSerializer
from projects.models import ProjectProposal

# Try to import reportlab, but handle gracefully if not installed
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ContractPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only client or freelancer involved in the contract can modify it
        return (obj.client == request.user or 
                obj.freelancer == request.user or 
                request.user.is_superuser)

class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = ContractPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Contract.objects.all().select_related(
                'project_proposal__project', 
                'project_proposal__freelancer'
            )
        elif user.user_type == 'client':
            return Contract.objects.filter(
                project_proposal__project__client=user
            ).select_related('project_proposal__project', 'project_proposal__freelancer')
        elif user.user_type == 'freelancer':
            return Contract.objects.filter(
                project_proposal__freelancer=user
            ).select_related('project_proposal__project', 'project_proposal__freelancer')
        return Contract.objects.none()

    def create(self, request, *args, **kwargs):
        """Create a contract from an accepted proposal"""
        proposal_id = request.data.get('proposal')
        if not proposal_id:
            return Response({'detail': 'proposal field is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            proposal = ProjectProposal.objects.get(id=proposal_id)
        except ProjectProposal.DoesNotExist:
            return Response({'detail': 'Proposal not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Only the client can create a contract
        if proposal.project.client != request.user and not request.user.is_superuser:
            return Response({'detail': 'Only the project owner can create contracts'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Proposal must be accepted
        if proposal.status != 'accepted':
            return Response({'detail': 'Only accepted proposals can be converted to contracts'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if contract already exists
        if hasattr(proposal, 'contract'):
            return Response({'detail': 'Contract already exists for this proposal'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create contract
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project_proposal=proposal)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_contracts(self, request):
        """Get contracts for current user"""
        user = request.user
        if user.user_type == 'client':
            queryset = Contract.objects.filter(
                project_proposal__project__client=user
            ).select_related('project_proposal__project', 'project_proposal__freelancer')
        elif user.user_type == 'freelancer':
            queryset = Contract.objects.filter(
                project_proposal__freelancer=user
            ).select_related('project_proposal__project', 'project_proposal__freelancer')
        else:
            queryset = Contract.objects.none()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        """Mark contract as completed"""
        contract = self.get_object()
        
        if contract.status != 'active':
            return Response({'detail': 'Only active contracts can be completed'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        contract.status = 'completed'
        contract.save()
        
        # Update project status
        project = contract.project
        project.status = 'completed'
        project.completed_at = date.today()
        project.save()
        
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel a contract"""
        contract = self.get_object()
        
        if contract.status != 'active':
            return Response({'detail': 'Only active contracts can be cancelled'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        contract.status = 'cancelled'
        contract.cancellation_reason = request.data.get('cancellation_reason', '')
        contract.save()
        
        # Update project status
        project = contract.project
        project.status = 'cancelled'
        project.save()
        
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def extend(self, request, pk=None):
        """Extend contract deadline"""
        contract = self.get_object()
        new_end_date = request.data.get('end_date')
        
        if not new_end_date:
            return Response({'detail': 'end_date is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        contract.end_date = new_end_date
        contract.save()
        
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def sign(self, request, pk=None):
        """Sign the contract"""
        contract = self.get_object()
        user = request.user
        
        if user == contract.client:
            contract.signed_by_client = True
        elif user == contract.freelancer:
            contract.signed_by_freelancer = True
        else:
            return Response({'detail': 'You are not authorized to sign this contract'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        contract.save()
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_document(self, request, pk=None):
        """Upload a document to the contract"""
        contract = self.get_object()
        file = request.FILES.get('document')
        
        if not file:
            return Response({'detail': 'No document provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        document = ContractDocument.objects.create(
            contract=contract,
            file=file,
            filename=file.name,
            uploaded_by=request.user,
            document_type=request.data.get('document_type', 'contract')
        )
        
        serializer = ContractDocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def documents(self, request, pk=None):
        """Get documents for a contract"""
        contract = self.get_object()
        documents = ContractDocument.objects.filter(contract=contract)
        serializer = ContractDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download_pdf(self, request, pk=None):
        """Download contract as PDF"""
        contract = self.get_object()
        
        if not REPORTLAB_AVAILABLE:
            # Fallback to simple text-based PDF generation
            return self.generate_simple_pdf(contract)
        
        # Create advanced PDF with reportlab
        return self.generate_advanced_pdf(contract)
    
    def generate_simple_pdf(self, contract):
        """Generate simple PDF without reportlab"""
        from django.http import HttpResponse
        
        # Create a simple text-based response
        content = f"""
CONTRACT DOCUMENT

Contract ID: {contract.id}
Project: {contract.project_proposal.project.title}
Client: {contract.client.first_name} {contract.client.last_name} ({contract.client.email})
Freelancer: {contract.freelancer.first_name} {contract.freelancer.last_name} ({contract.freelancer.email})

Contract Details:
- Total Payment: ${contract.total_payment}
- Start Date: {contract.start_date}
- End Date: {contract.end_date or 'Not specified'}
- Status: {contract.get_status_display()}

Deliverables:
{contract.deliverables or 'Not specified'}

Milestones:
{contract.milestones or 'Not specified'}

Signatures:
- Client Signed: {'Yes' if contract.signed_by_client else 'No'}
- Freelancer Signed: {'Yes' if contract.signed_by_freelancer else 'No'}

Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="contract-{contract.id}.txt"'
        return response
    
    def generate_advanced_pdf(self, contract):
        """Generate advanced PDF with reportlab"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("FREELANCE CONTRACT", title_style))
        story.append(Spacer(1, 20))
        
        # Contract Info Table
        contract_data = [
            ['Contract ID:', str(contract.id)],
            ['Date Created:', contract.created_at.strftime('%B %d, %Y')],
            ['Project:', contract.project_proposal.project.title],
            ['Status:', contract.get_status_display()],
        ]
        
        contract_table = Table(contract_data, colWidths=[2*inch, 4*inch])
        contract_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(contract_table)
        story.append(Spacer(1, 20))
        
        # Parties
        story.append(Paragraph("PARTIES", styles['Heading2']))
        
        parties_data = [
            ['CLIENT', 'FREELANCER'],
            [f"{contract.client.first_name} {contract.client.last_name}", 
             f"{contract.freelancer.first_name} {contract.freelancer.last_name}"],
            [contract.client.email, contract.freelancer.email],
            [f"User ID: {contract.client.id}", f"User ID: {contract.freelancer.id}"],
        ]
        
        parties_table = Table(parties_data, colWidths=[3*inch, 3*inch])
        parties_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(parties_table)
        story.append(Spacer(1, 20))
        
        # Financial Terms
        story.append(Paragraph("FINANCIAL TERMS", styles['Heading2']))
        
        financial_data = [
            ['Total Payment:', f"${contract.total_payment}"],
            ['Start Date:', contract.start_date.strftime('%B %d, %Y')],
            ['End Date:', contract.end_date.strftime('%B %d, %Y') if contract.end_date else 'Not specified'],
        ]
        
        financial_table = Table(financial_data, colWidths=[2*inch, 4*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(financial_table)
        story.append(Spacer(1, 20))
        
        # Deliverables
        if contract.deliverables:
            story.append(Paragraph("DELIVERABLES", styles['Heading2']))
            story.append(Paragraph(contract.deliverables, styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Milestones
        if contract.milestones:
            story.append(Paragraph("MILESTONES", styles['Heading2']))
            story.append(Paragraph(contract.milestones, styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Signatures
        story.append(Paragraph("SIGNATURES", styles['Heading2']))
        
        signature_data = [
            ['Party', 'Status', 'Date'],
            ['Client', 'Signed' if contract.signed_by_client else 'Pending', 
             contract.updated_at.strftime('%B %d, %Y') if contract.signed_by_client else ''],
            ['Freelancer', 'Signed' if contract.signed_by_freelancer else 'Pending',
             contract.updated_at.strftime('%B %d, %Y') if contract.signed_by_freelancer else ''],
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 2*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(signature_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Paragraph("This is a legally binding contract between the specified parties.", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contract-{contract.id}.pdf"'
        return response

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def analytics(self, request):
        """Get comprehensive contract analytics"""
        user = request.user
        
        # Base queryset based on user type
        if user.is_superuser:
            contracts = Contract.objects.all()
        elif user.user_type == 'client':
            contracts = Contract.objects.filter(project_proposal__project__client=user)
        elif user.user_type == 'freelancer':
            contracts = Contract.objects.filter(project_proposal__freelancer=user)
        else:
            contracts = Contract.objects.none()
        
        # Calculate statistics
        total_contracts = contracts.count()
        active_contracts = contracts.filter(status='active').count()
        completed_contracts = contracts.filter(status='completed').count()
        cancelled_contracts = contracts.filter(status='cancelled').count()
        
        # Financial statistics
        total_value = contracts.aggregate(total=Sum('total_payment'))['total'] or 0
        active_value = contracts.filter(status='active').aggregate(total=Sum('total_payment'))['total'] or 0
        completed_value = contracts.filter(status='completed').aggregate(total=Sum('total_payment'))['total'] or 0
        
        # Average contract value
        avg_value = total_value / total_contracts if total_contracts > 0 else 0
        
        # Monthly statistics
        current_month = timezone.now().replace(day=1)
        contracts_this_month = contracts.filter(created_at__gte=current_month).count()
        
        # Overdue contracts
        today = timezone.now().date()
        overdue_contracts = contracts.filter(
            status='active',
            end_date__lt=today
        ).count()
        
        # Recent activity
        recent_contracts = contracts.order_by('-created_at')[:5]
        
        # Contract status distribution
        status_distribution = contracts.values('status').annotate(
            count=Count('status')
        ).order_by('status')
        
        analytics_data = {
            'summary': {
                'total_contracts': total_contracts,
                'active_contracts': active_contracts,
                'completed_contracts': completed_contracts,
                'cancelled_contracts': cancelled_contracts,
                'total_value': total_value,
                'active_value': active_value,
                'completed_value': completed_value,
                'average_contract_value': avg_value,
                'contracts_this_month': contracts_this_month,
                'overdue_contracts': overdue_contracts,
            },
            'status_distribution': list(status_distribution),
            'recent_contracts': ContractSerializer(recent_contracts, many=True, context={'request': request}).data,
        }
        
        return Response(analytics_data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def sign_contract(self, request, pk=None):
        """Sign contract by client or freelancer"""
        contract = self.get_object()
        user = request.user
        
        # Check if user is authorized to sign
        if user == contract.client:
            if contract.signed_by_client:
                return Response(
                    {'error': 'Contract already signed by client'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            contract.signed_by_client = True
            contract.client_signed_at = timezone.now()
            
        elif user == contract.freelancer:
            if contract.signed_by_freelancer:
                return Response(
                    {'error': 'Contract already signed by freelancer'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            contract.signed_by_freelancer = True
            contract.freelancer_signed_at = timezone.now()
            
        else:
            return Response(
                {'error': 'Not authorized to sign this contract'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if both parties have signed
        if contract.signed_by_client and contract.signed_by_freelancer:
            if contract.status == 'draft':
                contract.status = 'active'
                contract.start_date = timezone.now().date()
                
                # Send notification to both parties
                from notifications.utils import create_notification
                create_notification(
                    user=contract.client,
                    title="Contract Activated",
                    message=f"Contract for project '{contract.project_proposal.project.title}' is now active",
                    notification_type="contract"
                )
                create_notification(
                    user=contract.freelancer,
                    title="Contract Activated",
                    message=f"Contract for project '{contract.project_proposal.project.title}' is now active",
                    notification_type="contract"
                )
        
        contract.save()
        
        serializer = ContractDetailSerializer(contract, context={'request': request})
        return Response({
            'message': f'Contract signed successfully by {user.get_full_name()}',
            'contract': serializer.data,
            'fully_signed': contract.signed_by_client and contract.signed_by_freelancer
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_milestone(self, request, pk=None):
        """Add milestone to contract"""
        contract = self.get_object()
        
        # Only allow contract parties to add milestones
        if request.user not in [contract.client, contract.freelancer]:
            return Response(
                {'error': 'Not authorized to modify this contract'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        milestone_data = request.data.get('milestone', {})
        if not milestone_data:
            return Response(
                {'error': 'Milestone data required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse existing milestones
        try:
            existing_milestones = json.loads(contract.milestones) if contract.milestones else []
        except (json.JSONDecodeError, TypeError):
            existing_milestones = []
        
        # Add new milestone
        new_milestone = {
            'id': len(existing_milestones) + 1,
            'title': milestone_data.get('title', ''),
            'description': milestone_data.get('description', ''),
            'amount': float(milestone_data.get('amount', 0)),
            'due_date': milestone_data.get('due_date', ''),
            'status': 'pending',
            'created_by': request.user.id,
            'created_at': timezone.now().isoformat(),
        }
        
        existing_milestones.append(new_milestone)
        contract.milestones = json.dumps(existing_milestones)
        contract.save()
        
        return Response({
            'message': 'Milestone added successfully',
            'milestone': new_milestone,
            'total_milestones': len(existing_milestones)
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete_milestone(self, request, pk=None):
        """Mark milestone as completed"""
        contract = self.get_object()
        milestone_id = request.data.get('milestone_id')
        
        if not milestone_id:
            return Response(
                {'error': 'Milestone ID required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only freelancer can mark milestones as completed
        if request.user != contract.freelancer:
            return Response(
                {'error': 'Only freelancer can mark milestones as completed'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Parse milestones
        try:
            milestones = json.loads(contract.milestones) if contract.milestones else []
        except (json.JSONDecodeError, TypeError):
            return Response(
                {'error': 'Invalid milestone data'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and update milestone
        milestone_found = False
        for milestone in milestones:
            if milestone.get('id') == int(milestone_id):
                milestone['status'] = 'completed'
                milestone['completed_at'] = timezone.now().isoformat()
                milestone['completed_by'] = request.user.id
                milestone_found = True
                break
        
        if not milestone_found:
            return Response(
                {'error': 'Milestone not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        contract.milestones = json.dumps(milestones)
        contract.save()
        
        # Send notification to client
        from notifications.utils import create_notification
        create_notification(
            user=contract.client,
            title="Milestone Completed",
            message=f"A milestone has been completed for project '{contract.project_proposal.project.title}'",
            notification_type="contract"
        )
        
        return Response({'message': 'Milestone marked as completed'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def extend_deadline(self, request, pk=None):
        """Extend contract deadline"""
        contract = self.get_object()
        
        # Only allow contract parties to extend deadline
        if request.user not in [contract.client, contract.freelancer]:
            return Response(
                {'error': 'Not authorized to modify this contract'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_end_date = request.data.get('end_date')
        reason = request.data.get('reason', '')
        
        if not new_end_date:
            return Response(
                {'error': 'New end date required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new date is after current end date
        if contract.end_date and new_end_date <= contract.end_date:
            return Response(
                {'error': 'New end date must be after current end date'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_end_date = contract.end_date
        contract.end_date = new_end_date
        contract.save()
        
        # Send notification to other party
        other_user = contract.client if request.user == contract.freelancer else contract.freelancer
        from notifications.utils import create_notification
        create_notification(
            user=other_user,
            title="Contract Deadline Extended",
            message=f"Contract deadline has been extended to {new_end_date} for project '{contract.project_proposal.project.title}'",
            notification_type="contract"
        )
        
        return Response({
            'message': 'Contract deadline extended successfully',
            'old_end_date': old_end_date,
            'new_end_date': new_end_date,
            'reason': reason
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def terminate_contract(self, request, pk=None):
        """Terminate contract with reason"""
        contract = self.get_object()
        
        # Only allow contract parties to terminate
        if request.user not in [contract.client, contract.freelancer]:
            return Response(
                {'error': 'Not authorized to terminate this contract'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow termination of active contracts
        if contract.status != 'active':
            return Response(
                {'error': 'Only active contracts can be terminated'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Termination reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contract.status = 'terminated'
        contract.termination_reason = reason
        contract.terminated_by = request.user
        contract.terminated_at = timezone.now()
        contract.save()
        
        # Send notification to other party
        other_user = contract.client if request.user == contract.freelancer else contract.freelancer
        from notifications.utils import create_notification
        create_notification(
            user=other_user,
            title="Contract Terminated",
            message=f"Contract for project '{contract.project_proposal.project.title}' has been terminated. Reason: {reason}",
            notification_type="contract"
        )
        
        return Response({
            'message': 'Contract terminated successfully',
            'termination_reason': reason,
            'terminated_by': request.user.get_full_name(),
            'terminated_at': contract.terminated_at
        })

    def get_permissions(self):
        """Enhanced permissions for all contract actions"""
        return [permissions.IsAuthenticated()]