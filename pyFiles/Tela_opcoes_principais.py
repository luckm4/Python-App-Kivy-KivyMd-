from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineListItem
from kivymd.uix.list import IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.app import MDApp
from kivy.properties import StringProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout

# Variaveis que executam comandos sql
sql_postgre    = None
sql_sqlite     = None

# Variaveis que configuram o sql
postgre_conn   = None
sqlite_conn    = None

# Variaveis de controle
usuarios = []
usuarios_unicos = set()
idades   = []
idades_unicas = set()

usuarios_bloqueados = {} # Dicionario que contem todos os usuarios bloqueados


user_adm_logado = None


class ListItemWithCheckbox(OneLineAvatarIconListItem):
    icon = StringProperty("android")

class Tela_opcoes_principais(MDScreen):
    dialog = None
    switch_bloqueado_selecionado = False
    switch = False
    # inicialização de variaveis de controle
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # Função que mostra um Popup na tela ajudando o usuário a compreender sobre o que a tela faz
    def ajuda(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Ajuda",
                type = "custom",
                text = '''Aqui é a tela onde as aplicações serão ativadas para cada bloqueado selecionado.\n
A opção "Configurações automáticas" vai alterar todos os horários dos usuários, ignorando assim o horário definido manualmente na janela aplicativos bloqueados''',
                auto_dismiss = False,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color = "Custom",
                        text_color = (0,0,0,1),
                        on_release=lambda x: self.fechar_dialog()
                    ),
                ],
            )
        self.dialog.open()
    # Função que fecha o Popup
    def fechar_dialog(self):
        self.dialog.dismiss()
        self.dialog = None

    # função que obtem informações do banco de dados sql
    def obter_dados(self, user):
        try:
            if sql_sqlite != None:
                # Obter Bloqueados ativos
                sql_sqlite.execute("SELECT bloqueados_ativos FROM usuarios_selecionados")
                nome_blo_db = sql_sqlite.fetchall()

                # Obter idade
                sql_sqlite.execute("SELECT idade_blo FROM bloqueados")
                linhas = sql_sqlite.fetchall()
                for linha in linhas:
                    for i in linha:
                        idades.append(i)


                        
                # if user not in usuarios_unicos:
                #     usuarios_unicos.add(user)
                #     # Item 4 da lista
                #     # Cria a lista de usuários com base em usuários cadastrados no banco de dados
                #     self.item = ListItemWithCheckbox(text=f"{user}", icon="face-man-profile")
                #     self.checkbox = RightCheckbox()
                #     for item_selecionado in nome_blo_db:
                #         if item_selecionado[0] == user:
                #             self.checkbox.active = True
                #     self.checkbox.bind(active=lambda x, y:self.bloqueado_selecionado(f"{user}", x, y))
                #     self.item.add_widget(self.checkbox)
                #     self.ids.container.add_widget(self.item)

                for idade in idades:
                    if idade not in idades_unicas:
                        idades_unicas.add(idade)
        except Exception as e:
            print(e)
    
    def bloqueado_selecionado(self, bloqueado, checkbox, value):
        if sql_sqlite != None:
            if value:
                sql_sqlite.execute(f"INSERT INTO usuarios_selecionados (bloqueados_ativos) VALUES ('{bloqueado}')")
                sqlite_conn.commit()
            else:
                sql = (f"DELETE FROM usuarios_selecionados WHERE bloqueados_ativos = ?")
                sql_sqlite.execute(sql, (bloqueado,))
                sqlite_conn.commit()

    # função executada ao sair da tela
    def on_leave(self):
        # limpa todas as listas
        usuarios.clear()
        idades.clear()
        usuarios_unicos.clear()
        idades_unicas.clear()
        self.ids.container.clear_widgets()


    # função que executa ao entrar na tela
    def on_enter(self):
        # # Item 1 da lista
        # item1 = ListItemWithCheckbox(text="Aplicar Configuração", icon="cog")
        # item1.bind(on_press=lambda x:self.configuracao_padrao())
        # self.ids.container.add_widget(item1)

        # EXEMPLO COM O CHECKBOX
    #     item1 = ListItemWithCheckbox(text="Aplicar Configuração Padrão", icon="cog")
    #     checkbox = RightCheckbox()
    #     checkbox.bind(active=lambda x, y:self.configuracao_padrao(x, y))
    #     item1.add_widget(checkbox)
    #     self.ids.container.add_widget(item1)
    #     def configuracao_padrao(self, checkbox, value):
    #         if value:
    #             if not self.dialog:
    #                 self.dialog = MDDialog(
    #                     title = "Aviso!",
    #                     text = '''Você está prestes a aplicar as configurações padrão do CEspreita, qualquer modificação feita em horários será perdida
    # você tem certeza que deseja alterar?''',
    #                     buttons = [
    #                         MDFlatButton(text="Não", on_release=lambda x:self.nao_configurar(checkbox)),
    #                         MDFlatButton(text="Sim", on_release=lambda x:self.sim_configurar(checkbox))
    #                     ]
    #                 )
    #             self.dialog.open()
        
        # Item 2 da lista
        item1 = ListItemWithCheckbox(text="Configurações automáticas", icon="cog")
        item1.bind(on_press=lambda x:self.configuracao_padrao())
        self.ids.container.add_widget(item1)

        
        # logo depois de criar os primeiros itens, chama a função que obtem dados do sql
        # Obter nome
        sql_sqlite.execute("SELECT nome_blo FROM bloqueados")
        linhas = sql_sqlite.fetchall()
        for linha in linhas:
            for i in linha:
                usuarios.append(i)
        for user in usuarios:
            self.obter_dados(user)
    

    # Fechar o dialogo e desativar o checkbox
    def nao_configurar(self):
        self.dialog.dismiss()
        self.dialog = None
    
    # Fecha o dialogo, ativa o checkbox e configura os horários
    def sim_configurar(self):
        self.dialog.dismiss()
        self.dialog = None

    # Aplica as configurações padrão do CEspreita
    def configuracao_padrao(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Aviso!",
                text = '''Você está prestes a aplicar as configurações padrão do CEspreita, qualquer modificação feita em horários será perdida
você tem certeza que deseja alterar?''',
                buttons = [
                    MDFlatButton(text="Não", on_release=lambda x:self.nao_configurar()),
                    MDFlatButton(text="Sim", on_release=lambda x:self.sim_configurar())
                ]
            )
        self.dialog.open()
    
    # Função que muda os horários de todos os bloqueados selecionados
    def mudar_horario(self):
        pass
        
    # Função que restaura as configurações do usuario selecionado
    def restaurar_configuracoes(self, checkbox, value):
        if value:
            print("configurações resetadas")
        else:
            print("configurações não resetadas")

class RightCheckbox(IRightBodyTouch, MDCheckbox):
    pass
