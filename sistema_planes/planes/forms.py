"""
Formularios para el sistema de planes de mejoramiento
"""
from django import forms
from django.forms import formset_factory
from .models import PlanMejoramiento, AccionMejora, DocumentoPlan


class LoginForm(forms.Form):
    """Formulario de login"""
    username = forms.CharField(
        label='Usuario (NIT para proveedores)',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su usuario o NIT',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )


class PlanMejoramientoForm(forms.ModelForm):
    """Formulario para crear/editar plan de mejoramiento"""
    
    class Meta:
        model = PlanMejoramiento
        fields = [
            'analisis_causa',
            'acciones_propuestas', 
            'responsable',
            'fecha_implementacion',
            'indicadores_seguimiento'
        ]
        widgets = {
            'analisis_causa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describa detalladamente las causas raíz de los problemas identificados...',
                'required': True
            }),
            'acciones_propuestas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detalle las acciones de mejora propuestas...',
                'required': True
            }),
            'responsable': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del responsable principal',
                'required': True
            }),
            'fecha_implementacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'indicadores_seguimiento': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa los indicadores para medir el éxito de las acciones...',
                'required': True
            })
        }
    
    def clean_analisis_causa(self):
        analisis = self.cleaned_data.get('analisis_causa')
        if len(analisis) < 100:
            raise forms.ValidationError(
                'El análisis de causa debe tener al menos 100 caracteres.'
            )
        return analisis
    
    def clean_fecha_implementacion(self):
        from datetime import date
        fecha = self.cleaned_data.get('fecha_implementacion')
        if fecha and fecha < date.today():
            raise forms.ValidationError(
                'La fecha de implementación no puede ser en el pasado.'
            )
        return fecha


class AccionMejoraForm(forms.ModelForm):
    """Formulario para acciones de mejora individuales"""
    
    class Meta:
        model = AccionMejora
        fields = ['descripcion', 'responsable', 'fecha_compromiso', 'indicador']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la acción'
            }),
            'responsable': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Responsable'
            }),
            'fecha_compromiso': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'indicador': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Indicador de éxito'
            })
        }


# Formset para múltiples acciones
AccionMejoraFormSet = formset_factory(
    AccionMejoraForm,
    extra=3,
    can_delete=True
)


class DocumentoPlanForm(forms.ModelForm):
    """Formulario para adjuntar documentos"""
    
    class Meta:
        model = DocumentoPlan
        fields = ['archivo', 'nombre', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del documento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción opcional'
            })
        }


class RevisionPlanForm(forms.Form):
    """Formulario para la revisión del técnico"""
    
    DECISIONES = [
        ('', '-- Seleccione una decisión --'),
        ('APROBADO', 'Aprobar Plan'),
        ('REQUIERE_AJUSTES', 'Solicitar Ajustes'),
        ('RECHAZADO', 'Rechazar Plan')
    ]
    
    decision = forms.ChoiceField(
        label='Decisión',
        choices=DECISIONES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    comentarios = forms.CharField(
        label='Comentarios para el proveedor',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Escriba sus observaciones y comentarios para el proveedor...',
            'required': True
        })
    )
    
    def clean_comentarios(self):
        comentarios = self.cleaned_data.get('comentarios')
        decision = self.cleaned_data.get('decision')
        
        if decision in ['REQUIERE_AJUSTES', 'RECHAZADO'] and len(comentarios) < 50:
            raise forms.ValidationError(
                'Debe proporcionar comentarios detallados al solicitar ajustes o rechazar.'
            )
        return comentarios