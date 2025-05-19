from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization

class AIConversation(models.Model):
    class ConversationType(models.TextChoices):
        GENERAL = 'general', _('General')
        FINANCIAL = 'financial', _('Financial')
        BUDGETING = 'budgeting', _('Budgeting')
        FORECASTING = 'forecasting', _('Forecasting')
        ANALYSIS = 'analysis', _('Analysis')
        RECOMMENDATION = 'recommendation', _('Recommendation')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('organization')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('user')
    )
    
    type = models.CharField(
        _('type'),
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.GENERAL
    )
    title = models.CharField(_('title'), max_length=255)
    
    # Context and state
    context = models.JSONField(_('context'), default=dict)
    current_state = models.JSONField(_('current state'), default=dict)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('AI conversation')
        verbose_name_plural = _('AI conversations')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} - {self.title}"

class AIMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', _('User')
        ASSISTANT = 'assistant', _('Assistant')
        SYSTEM = 'system', _('System')

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices
    )
    content = models.TextField(_('content'))
    
    # Additional data
    data = models.JSONField(_('data'), default=dict, blank=True)
    tokens_used = models.IntegerField(_('tokens used'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    processed = models.BooleanField(_('processed'), default=False)

    class Meta:
        verbose_name = _('AI message')
        verbose_name_plural = _('AI messages')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"

class AIInsight(models.Model):
    class InsightType(models.TextChoices):
        SPENDING_PATTERN = 'spending_pattern', _('Spending Pattern')
        BUDGET_ALERT = 'budget_alert', _('Budget Alert')
        SAVING_OPPORTUNITY = 'saving_opportunity', _('Saving Opportunity')
        INVESTMENT_SUGGESTION = 'investment_suggestion', _('Investment Suggestion')
        CASH_FLOW_PREDICTION = 'cash_flow_prediction', _('Cash Flow Prediction')
        ANOMALY_DETECTION = 'anomaly_detection', _('Anomaly Detection')
        TAX_OPTIMIZATION = 'tax_optimization', _('Tax Optimization')

    class Severity(models.TextChoices):
        INFO = 'info', _('Information')
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='ai_insights',
        verbose_name=_('organization')
    )
    type = models.CharField(
        _('type'),
        max_length=30,
        choices=InsightType.choices
    )
    
    # Content
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    data = models.JSONField(_('data'), default=dict)
    
    # Classification
    severity = models.CharField(
        _('severity'),
        max_length=20,
        choices=Severity.choices,
        default=Severity.INFO
    )
    confidence_score = models.FloatField(
        _('confidence score'),
        default=0.0,
        help_text=_('AI confidence in this insight (0-1)')
    )
    
    # Validity
    valid_from = models.DateTimeField(_('valid from'), auto_now_add=True)
    valid_until = models.DateTimeField(_('valid until'), null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Action tracking
    action_taken = models.BooleanField(_('action taken'), default=False)
    action_taken_at = models.DateTimeField(_('action taken at'), null=True, blank=True)
    action_taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_taken',
        verbose_name=_('action taken by')
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('AI insight')
        verbose_name_plural = _('AI insights')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'type', '-created_at']),
            models.Index(fields=['organization', 'severity', '-created_at']),
        ]

    def __str__(self):
        return f"{self.organization} - {self.title}"

    def mark_as_actioned(self, user):
        from django.utils import timezone
        self.action_taken = True
        self.action_taken_at = timezone.now()
        self.action_taken_by = user
        self.save(update_fields=['action_taken', 'action_taken_at', 'action_taken_by'])

class AIRecommendation(models.Model):
    class RecommendationType(models.TextChoices):
        BUDGET_ADJUSTMENT = 'budget_adjustment', _('Budget Adjustment')
        EXPENSE_REDUCTION = 'expense_reduction', _('Expense Reduction')
        INVESTMENT = 'investment', _('Investment')
        SAVINGS = 'savings', _('Savings')
        DEBT_MANAGEMENT = 'debt_management', _('Debt Management')
        TAX_PLANNING = 'tax_planning', _('Tax Planning')
        CASH_FLOW = 'cash_flow', _('Cash Flow')

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='ai_recommendations',
        verbose_name=_('organization')
    )
    type = models.CharField(
        _('type'),
        max_length=30,
        choices=RecommendationType.choices
    )
    
    # Content
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    rationale = models.TextField(_('rationale'))
    potential_impact = models.TextField(_('potential impact'))
    
    # Data
    data = models.JSONField(_('data'), default=dict)
    metrics = models.JSONField(
        _('metrics'),
        default=dict,
        help_text=_('Quantifiable metrics for this recommendation')
    )
    
    # Status
    is_implemented = models.BooleanField(_('implemented'), default=False)
    implementation_notes = models.TextField(_('implementation notes'), blank=True)
    implemented_at = models.DateTimeField(_('implemented at'), null=True, blank=True)
    implemented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='implemented_recommendations',
        verbose_name=_('implemented by')
    )
    
    # Follow-up
    follow_up_date = models.DateField(_('follow up date'), null=True, blank=True)
    follow_up_notes = models.TextField(_('follow up notes'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('AI recommendation')
        verbose_name_plural = _('AI recommendations')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization} - {self.title}"

    def mark_as_implemented(self, user, notes=''):
        from django.utils import timezone
        self.is_implemented = True
        self.implementation_notes = notes
        self.implemented_at = timezone.now()
        self.implemented_by = user
        self.save(update_fields=[
            'is_implemented',
            'implementation_notes',
            'implemented_at',
            'implemented_by'
        ])

class AIModel(models.Model):
    class ModelType(models.TextChoices):
        CLASSIFICATION = 'classification', _('Classification')
        REGRESSION = 'regression', _('Regression')
        FORECASTING = 'forecasting', _('Forecasting')
        CLUSTERING = 'clustering', _('Clustering')
        ANOMALY_DETECTION = 'anomaly_detection', _('Anomaly Detection')

    name = models.CharField(_('name'), max_length=255)
    type = models.CharField(
        _('type'),
        max_length=30,
        choices=ModelType.choices
    )
    description = models.TextField(_('description'))
    
    # Model details
    version = models.CharField(_('version'), max_length=50)
    parameters = models.JSONField(_('parameters'), default=dict)
    metrics = models.JSONField(_('metrics'), default=dict)
    
    # Training information
    last_trained = models.DateTimeField(_('last trained'), null=True, blank=True)
    training_duration = models.DurationField(_('training duration'), null=True, blank=True)
    training_data_range = models.JSONField(
        _('training data range'),
        default=dict,
        help_text=_('Start and end dates of training data')
    )
    
    # Performance tracking
    accuracy = models.FloatField(_('accuracy'), null=True, blank=True)
    error_rate = models.FloatField(_('error rate'), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_production = models.BooleanField(_('in production'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('AI model')
        verbose_name_plural = _('AI models')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version}"
