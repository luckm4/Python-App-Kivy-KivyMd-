from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRectangleFlatIconButton
from kivy.uix.screenmanager import SlideTransition
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp
import configparser
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass


sql_postgre          = None
postgre_conn         = None

sql_sqlite           = None
sqlite_conn          = None

user_adm_logado      = None

bloqueado_selecionado = "" # Váriavel de controle do bloqueado


# Função para salvar ou atualizar o valor de uma variável em um arquivo de configuração
#########################################################################################################
def save_config_value(filename, section, variable_name, variable_value):
    config = configparser.ConfigParser()
    config.read(filename)
    if section not in config:
        config.add_section(section)
    config.set(section, variable_name, str(variable_value))
    with open(filename, 'w') as config_file:
        config.write(config_file)

# Função para ler o valor de uma variável de um arquivo de configuração
def read_config_value(filename, section, variable_name):
    config = configparser.ConfigParser()
    config.read(filename)
    if section in config and variable_name in config[section]:
        return config.get(section, variable_name)
    else:
        return None
#########################################################################################################



# Função que quando chamada armazena os nomes dos bloqueados que estão atualmente ativos na váriavel "bloqueado_selecionado"
#########################################################################################################
def obter_bloqueados_ativos():
    global bloqueado_selecionado
    if sql_sqlite:
        sql_sqlite.execute("SELECT bloqueados_ativos FROM usuarios_selecionados")
        nome_blo_db = sql_sqlite.fetchall()
        # Criar uma lista temporária para armazenar os nomes dos bloqueados do banco de dados
        bloqueados_db = []
        # Iterar sobre os bloqueados ativos do banco de dados
        for i in nome_blo_db:
            nome_bloqueado = f'{i[0]}/'
            bloqueados_db.append(nome_bloqueado)
            # Verificar se o nome do bloqueado já está na variável
            if nome_bloqueado not in bloqueado_selecionado:
                bloqueado_selecionado += nome_bloqueado
        # Verificar se algum bloqueado foi removido do banco de dados
        for bloqueado in bloqueado_selecionado.split('/'):
            if bloqueado and bloqueado + '/' not in bloqueados_db:
                # Remover o bloqueado que não está mais ativo do banco de dados
                bloqueado_selecionado = bloqueado_selecionado.replace(bloqueado + '/', '')
#########################################################################################################


# Função que obtem o nome do pacote pelo nome do app exibido
#########################################################################################################
def obter_pacote(nome_do_app):
    if platform == 'android':
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        PackageManager = autoclass('android.content.pm.PackageManager')
        Intent = autoclass('android.content.Intent')

        package_manager = PythonActivity.mActivity.getPackageManager()
        intent = Intent(Intent.ACTION_MAIN, None)
        intent.addCategory(Intent.CATEGORY_LAUNCHER)
        apps_list = package_manager.queryIntentActivities(intent, 0)

        for app in apps_list:
            if app.loadLabel(package_manager) == nome_do_app:
                return app.activityInfo.packageName
        return None
#########################################################################################################



# Função que retorna uma lista de todos os apps que não são do sistema
#########################################################################################################
def list_apps():
    if platform == 'android':
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            PackageManager = autoclass('android.content.pm.PackageManager')
            ComponentName = autoclass('android.content.ComponentName')
            Build = autoclass('android.os.Build')
            activity = PythonActivity.mActivity
            package_manager = activity.getPackageManager()
            # Criar um intent para listar todos os aplicativos
            intent = Intent(Intent.ACTION_MAIN)
            intent.addCategory(Intent.CATEGORY_LAUNCHER)
            # Obter a lista de atividades que correspondem ao intent
            activities = package_manager.queryIntentActivities(intent, 0)
            user_apps = []
            # Iterar sobre as atividades encontradas
            for activity in activities:
                app_info = activity.activityInfo
                # Verificar se o aplicativo não é do sistema
                if not (app_info.applicationInfo.flags & app_info.applicationInfo.FLAG_SYSTEM):
                    app_name = app_info.loadLabel(package_manager)
                    user_apps.append(app_name)
            return user_apps
        except Exception as e:
            print("Erro ao listar aplicativos:", e)
    else:
        return ['app_1', 'app_2', 'app_3']
#########################################################################################################


# CLASSE TELA PRICIPAL
class TelaPrincipal(MDScreen):
    global sql_postgre, postgre_conn, sql_sqlite, sqlite_conn
    dialog             = None
    switch_config      = False
    switch_bloqueados  = False
    switch_conta       = False
    switch_bisbilhotar = False
    switch_avisos      = False
    switch_theme       = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_enter(self):
        global bloqueado_selecionado, user_adm_logado
        if read_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "obter_bloqueados") == "False":
            if platform == 'android':
                save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "obter_bloqueados", "True")
            else:
                pass
            obter_bloqueados_ativos()
            lista_apps = list_apps()
            for app in lista_apps:
                nome_do_pacote = obter_pacote(app)
                if sql_sqlite:
                    # Verifique se a informação já existe na tabela aplic_bloc
                    sql_sqlite.execute(f"SELECT * FROM aplic_bloc WHERE nome_apl = '{app}'")
                    resultado = sql_sqlite.fetchall()
                    # Se a informação não existir na tabela, você pode adicionar
                    if not resultado:
                        try:
                            sql_sqlite.execute(f'''
                                INSERT INTO aplic_bloc (
                                codigo_apl,
                                nome_apl,
                                tip_bloq_apl,
                                bloc_horario_unico,
                                ap_hor1_apl,
                                ap_hor2_apl,
                                ap_hor3_apl,
                                ap_hor4_apl,
                                at_hor1_apl,
                                ap_hor2_apl,
                                ap_hor3_apl,
                                ap_hor4_apl) VALUES (
                                "{nome_do_pacote}",
                                "{app}",
                                'BLOQUEADO_INDETERMINADO',
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL",
                                "NULL");''') # Adiciona o app no banco de dados sql
                            sqlite_conn.commit()
                        except:
                            pass
                    else:
                        pass # O aplicativo já existe na tabela
                    sql_sqlite.execute(f"SELECT * FROM listaapps WHERE nome_apps = '{app}' AND nome_adm = '{user_adm_logado}' AND nome_blo = '{bloqueado_selecionado}'")
                    resultado = sql_sqlite.fetchall()
                    # # Se a informação não existir na tabela, você pode adicionar
                    if not resultado:
                        try:
                            sql_sqlite.execute(f"INSERT INTO listaapps (nome_apps, nome_adm, nome_blo) VALUES ('{app}', '{user_adm_logado}', '{bloqueado_selecionado}')")
                            sqlite_conn.commit()
                        except:
                            pass
                    else:
                        pass # O aplicativo já existe na tabela
        




    def on_pre_enter(self):
        if sql_sqlite != None:
            sql_sqlite.execute("SELECT idade_blo FROM bloqueados")
            resultado = sql_sqlite.fetchone()
            if resultado == None:
                self.manager.current = "tela_cadbloqueados"
                if not self.dialog:
                    self.dialog = MDDialog(
                        title="Aviso!",
                        text="Cadastre um bloqueado!",
                        buttons=[
                            MDFlatButton(
                                text="OK",
                                on_release=lambda x: self.dialog.dismiss()
                            ),
                        ],
                    )
                self.dialog.open()

    def theme_style(self):
        self.close_menu()
        self.switch_theme = not self.switch_theme
        if self.switch_theme:
            MDApp.get_running_app().theme_cls.theme_style = "Dark"
            self.ids.theme_btn_id.right_action_items = [["lightbulb-off-outline", lambda x:self.theme_style()]]
        else:
            MDApp.get_running_app().theme_cls.theme_style = "Light"
            self.ids.theme_btn_id.right_action_items = [["lightbulb-on-10", lambda x:self.theme_style()]]

    def mudar_janela(self, nome_janela):
        self.switch_avisos = not self.switch_avisos
        self.manager.transition = SlideTransition()
        self.manager.transition.direction = "up"
        self.manager.current = nome_janela
    def opcoes_bisbilhotar(self):
        self.switch_bisbilhotar = not self.switch_bisbilhotar
        if self.switch_bisbilhotar:
            self.ids.drawer_bisb1.adaptive_height = True
            self.ids.drawer_bisb2.adaptive_height = True
            self.ids.drawer_bisb3.adaptive_height = True
            self.ids.drawer_bisb4.adaptive_height = True
            self.ids.drawer_bisb5.adaptive_height = True
            self.bt1 = (
                            MDRectangleFlatIconButton(
                                id = 'item1',
                                text = "  Localização",
                                icon = "google-maps",
                                halign = 'right',
                                padding = ['18dp', '8dp', '135dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.bt2 = (
                            MDRectangleFlatIconButton(
                                id = 'item2',
                                text = "  Cameras e Audio",
                                icon = "camcorder",
                                halign = 'right',
                                padding = ['18dp', '8dp', '100dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.bt3 = (
                            MDRectangleFlatIconButton(
                                id = 'item3',
                                text = "  Histórico",
                                icon = "history",
                                halign = 'right',
                                padding = ['18dp', '8dp', '155dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.bt4 = (
                            MDRectangleFlatIconButton(
                                id = 'item4',
                                text = "  Galeria",
                                icon = "view-gallery",
                                halign = 'right',
                                padding = ['18dp', '8dp', '170dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.bt5 = (
                            MDRectangleFlatIconButton(
                                id = 'item5',
                                text = "  Programas Instalados",
                                icon = "application-brackets",
                                halign = 'right',
                                padding = ['18dp', '8dp', '70dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.ids.drawer_bisb1.add_widget(self.bt1)
            self.ids.drawer_bisb2.add_widget(self.bt2)
            self.ids.drawer_bisb3.add_widget(self.bt3)
            self.ids.drawer_bisb4.add_widget(self.bt4)
            self.ids.drawer_bisb5.add_widget(self.bt5)
        else:
            try:
                self.ids.drawer_bisb1.clear_widgets()
                self.ids.drawer_bisb2.clear_widgets()
                self.ids.drawer_bisb3.clear_widgets()
                self.ids.drawer_bisb4.clear_widgets()
                self.ids.drawer_bisb5.clear_widgets()
            except:
                pass






    def opcoes_conta(self):
        self.switch_conta = not self.switch_conta
        if self.switch_conta:
            self.ids.drawer_cont2.adaptive_height = True
            self.ids.drawer_cont3.adaptive_height = True
            self.bt2 = (
                            MDRectangleFlatIconButton(
                                id = 'item2',
                                text = "  Alterar Senha",
                                icon = "account-lock",
                                halign = 'right',
                                padding = ['18dp', '8dp', '125dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.bt3 = (
                            MDRectangleFlatIconButton(
                                id = 'item3',
                                text = "  Plano de Pagamento",
                                icon = "cash",
                                halign = 'right',
                                padding = ['18dp', '8dp', '78dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                            ))
            self.ids.drawer_cont2.add_widget(self.bt2)
            self.ids.drawer_cont3.add_widget(self.bt3)
        else:
            try:
                self.ids.drawer_cont2.clear_widgets()
                self.ids.drawer_cont3.clear_widgets()
            except:
                pass


            

    def opcoes_bloqueados(self):
        self.switch_bloqueados = not self.switch_bloqueados
        if self.switch_bloqueados:
            self.ids.drawer_bloq1.adaptive_height = True
            self.ids.drawer_bloq2.adaptive_height = True
            self.ids.drawer_bloq3.adaptive_height = True
            self.ids.drawer_bloq4.adaptive_height = True
            self.ids.drawer_bloq5.adaptive_height = True
            self.bt1 = (MDRectangleFlatIconButton(
                                id = 'item1',
                                text = "  Cadastro dos Bloqueados",
                                icon = "account-cancel",
                                halign = 'right',
                                padding = ['18dp', '8dp', '39dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                on_release = lambda x:self.mudar_janela("tela_cadbloqueados")
                            ))


            
            self.bt2 = (MDRectangleFlatIconButton(
                                id = 'item2',
                                text = "  Principal",
                                icon = "list-status",
                                halign = 'right',
                                padding = ['18dp', '8dp', '155dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                on_release = lambda x:self.mudar_janela("tela_opcoes_principais")
                            ))


            
            self.bt3 = (MDRectangleFlatIconButton(
                                id = 'item3',
                                text = "  Sites Bloqueados",
                                icon = "cellphone-link-off",
                                halign = 'right',
                                padding = ['18dp', '8dp', '95dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                on_release = lambda x:self.mudar_janela("sites_bloqueados")
                            ))


            
            self.bt4 = (MDRectangleFlatIconButton(
                                id = 'item4',
                                text = "  Aplicativos Bloqueados",
                                icon = "apps",
                                halign = 'right',
                                padding = ['18dp', '8dp', '53dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                on_release = lambda x:self.mudar_janela('tela_lista_apps')
                            ))
            self.ids.drawer_bloq1.add_widget(self.bt1)
            self.ids.drawer_bloq2.add_widget(self.bt2)
            self.ids.drawer_bloq3.add_widget(self.bt3)
            self.ids.drawer_bloq4.add_widget(self.bt4)


        else:
            try:
                self.ids.drawer_bloq1.clear_widgets()
                self.ids.drawer_bloq2.clear_widgets()
                self.ids.drawer_bloq3.clear_widgets()
                self.ids.drawer_bloq4.clear_widgets()
            except:
                pass


    def opcoes_configura(self):
        self.switch_config = not self.switch_config
        if self.switch_config:
            self.ids.drawer_conf1.opacity = 1
            self.ids.drawer_conf2.opacity = 1
            self.ids.drawer_conf3.opacity = 1
            self.bt1 = (MDRectangleFlatIconButton(
                                id = 'item1',
                                text = "  Avisos!",
                                icon = "alert",
                                halign = 'right',
                                padding = ['18dp', '8dp', '160dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                opacity = 1,
                                on_release=lambda x:self.mudar_janela("tela_alerta")
                            ))


            self.bt2 = (MDRectangleFlatIconButton(
                                id = 'item2',
                                text = "  Tela",
                                icon = "cellphone",
                                halign = 'right',
                                padding = ['18dp', '8dp', '183dp', '17dp'],
                                font_size = '15sp',
                                icon_size = '22sp',
                                opacity = 1,
                                theme_text_color = "Custom",
                                line_color = MDApp.get_running_app().theme_cls.bg_light,
                                size_hint = (1, None),
                                on_release=lambda x:self.mudar_janela("tela_tela")
                            ))
            self.ids.drawer_conf1.adaptive_height = True
            self.ids.drawer_conf2.adaptive_height = True
            self.ids.drawer_conf1.add_widget(self.bt1)
            self.ids.drawer_conf2.add_widget(self.bt2)
            if self.switch_avisos:
                pass
        else:
            try:
                self.ids.drawer_conf1.clear_widgets()
                self.ids.drawer_conf2.clear_widgets()
            except:
                pass


    def remove_widget(self):
        self.ids.drawer_conf1.adaptive_height = False
        self.ids.drawer_conf2.adaptive_height = False
        self.ids.nav_drawer.set_state("open")

    def close_menu(self):
        self.ids.nav_drawer.set_state("close")
        self.switch_config      = False
        self.switch_bloqueados  = False
        self.switch_conta       = False
        self.switch_bisbilhotar = False
        self.switch_avisos      = False
        try:
            self.ids.drawer_bisb1.clear_widgets()
            self.ids.drawer_bisb2.clear_widgets()
            self.ids.drawer_bisb3.clear_widgets()
            self.ids.drawer_bisb4.clear_widgets()
            self.ids.drawer_bisb5.clear_widgets()
            self.ids.drawer_cont2.clear_widgets()
            self.ids.drawer_cont3.clear_widgets()
            self.ids.drawer_bloq1.clear_widgets()
            self.ids.drawer_bloq2.clear_widgets()
            self.ids.drawer_bloq3.clear_widgets()
            self.ids.drawer_bloq4.clear_widgets()
            self.ids.drawer_conf1.clear_widgets()
            self.ids.drawer_conf2.clear_widgets()
        except:
            pass