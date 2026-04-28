from django.urls import path
from . import views

app_name = 'kanban'

urlpatterns = [
    path('kanban/', views.kanban_producao, name='producao'),
    path('minhas-tarefas/', views.minhas_tarefas, name='minhas_tarefas'),
    path('etapa/<int:etapa_id>/mover/', views.mover_etapa, name='mover_etapa'),
    path('etapa/<int:etapa_id>/atribuir/', views.atribuir_funcionario, name='atribuir_funcionario'),
    path('etapa/<int:etapa_id>/reprogramar/', views.reprogramar_etapa, name='reprogramar_etapa'),
    path('etapa/<int:etapa_id>/iniciar/', views.iniciar_tarefa, name='iniciar_tarefa'),
    path('etapa/<int:etapa_id>/concluir/', views.concluir_tarefa, name='concluir_tarefa'),
    # Novas rotas de sessão de trabalho
    path('etapa/<int:etapa_id>/sessao/iniciar/', views.sessao_iniciar, name='sessao_iniciar'),
    path('etapa/<int:etapa_id>/sessao/pausar/', views.sessao_pausar, name='sessao_pausar'),
    path('etapa/<int:etapa_id>/sessao/finalizar/', views.sessao_finalizar, name='sessao_finalizar'),
    path('etapa/<int:etapa_id>/extra/toggle/', views.etapa_toggle_extra, name='etapa_toggle_extra'),
    path('ordem/<int:ordem_id>/entregar/', views.entregar_ordem, name='entregar_ordem'),
    path('agenda/', views.agenda_producao, name='agenda'),
    path('agenda-mao-de-obra/', views.agenda_mao_obra, name='agenda_mao_obra'),
    path('debug-etapas/', views.debug_etapas, name='debug_etapas'),
]
