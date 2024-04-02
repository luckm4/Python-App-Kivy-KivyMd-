from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.uix.screenmanager import RiseInTransition
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp
from kivy.clock import Clock, mainthread
from datetime import datetime
import threading
import time
import configparser
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, cast

####################################---VÁRIAVEIS---####################################
# Variaveis que executam comandos sql
sql_postgre    = None
sql_sqlite     = None

# Variaveis que configuram o sql
postgre_conn   = None
sqlite_conn    = None

adm_existente = ""

get_process = False

debbug_mode = False
#######################################################################################





# Função para salvar ou atualizar o valor de uma variável em um arquivo de configuração
#######################################################################################
def save_config_value(filename, section, variable_name, variable_value):
    config = configparser.ConfigParser()
    config.read(filename)
    if section not in config:
        config.add_section(section)
    config.set(section, variable_name, str(variable_value))
    with open(filename, 'w') as config_file:
        config.write(config_file)
#######################################################################################



# Função para ler o valor de uma variável de um arquivo de configuração
#######################################################################################
def read_config_value(filename, section, variable_name):
    config = configparser.ConfigParser()
    config.read(filename)
    if section in config and variable_name in config[section]:
        return config.get(section, variable_name)
    else:
        return None
#######################################################################################



# Classe da tela de informações sobre o bloqueado
#######################################################################################
class Info_bloqueado(MDBoxLayout):
    dialog = None
    adm_encontrado = False
    data_mensagem = ""
    data_check = False
    
    # Função que checa as credencias do administrador para verificar se são válidas
    def verificar_credenciais(self, usuario, senha):
        global sql_sqlite, sqlite_conn
        # Executar uma consulta para verificar se o usuário e senha são válidos
        sql_sqlite.execute("SELECT * FROM administrador WHERE nome_adm = ? AND senha_adm = ?", (usuario, senha))
        # Recuperar o primeiro resultado da consulta (se existir)
        resultado = sql_sqlite.fetchone()
        # Verificar se as credenciais são válidas
        if resultado:
            return True
        else:
            return False

    # Popup do bloqueado, se for bloqueado pergunta o nome, nome do adm etc
    def open_dialog(self):
        # Desabilita os botões ao cadastrar o usuário
        try:
            MDApp.get_running_app().root.get_screen('tela_login').ids.campo_usuario.disabled = True
            MDApp.get_running_app().root.get_screen('tela_login').ids.campo_senha.disabled = True
            MDApp.get_running_app().root.get_screen('tela_login').ids.botao_entrar.disabled = True
            MDApp.get_running_app().root.get_screen('tela_login').ids.botao_cadastrar.disabled = True
        except:
            pass
        if not self.dialog:
            self.dialog = MDDialog(
                type = "custom",
                content_cls = self,
                auto_dismiss=False,
                height=500,
                buttons = [
                    MDRaisedButton(
                        text="Voltar",
                        md_bg_color = (1,1,1,1),
                        theme_text_color = "Custom",
                        text_color = (0,0,0,1),
                        on_release = lambda x:self.voltar()),
                    MDRaisedButton(
                        text="Ok",
                        md_bg_color = (1,1,1,1),
                        theme_text_color = "Custom",
                        text_color = (0,0,0,1),
                        on_release = lambda x:self.save_sql_info())
                ]
            )
        self.dialog.open()
        threading.Thread(target=self.start_thread_set_text).start()
    
    # Threading simples para iniciar a checagem de texto
    def start_thread_set_text(self):
        while MDApp.get_running_app():
            time.sleep(0.1)
            self.set_text()
    
    # Thread iniciada para corrigir o texto da data, adicionando barras nos pontos certos
    @mainthread
    def set_text(self):
        try:
            data_nasc = self.ids.idade_blo
            self.data_text_1 = data_nasc.text
            if len(data_nasc.text) == 2 and self.barra_1 == False:
                self.barra_1 = True
                self.ids.idade_blo.text = (f"{self.data_text_1}/")
            if len(data_nasc.text) == 5 and self.barra_2 == False:
                self.barra_2 = True
                self.ids.idade_blo.text = (f"{self.data_text_1}/")
            if len(data_nasc.text) < 2 > 1:
                self.barra_1 = False
            if len(data_nasc.text) < 5 > 4:
                self.barra_2 = False
        except:
            pass

    # Função que checa a formatação da data e diz se é válida
    def checar_data(self, data):
        def obter_data(data):
            try:
                data_nascimento = datetime.strptime(data, "%d/%m/%Y") #Define o formato da data
                data_limite = datetime(1900, 1, 1)  # Defina a data limite aqui
                if data_nascimento > datetime.now(): # Não pode ser maior que a data atual
                    return False, "A data de nascimento não pode ser no futuro."
                if data_nascimento < data_limite:
                    return False, "A data de nascimento é anterior a 1900 e não é válida."
                    #Calcula a idade
                idade = datetime.now().year - data_nascimento.year - ((datetime.now().month, datetime.now().day) < (data_nascimento.month, data_nascimento.day))
                return True, f"Idade: {idade} anos"
            except ValueError:
                return False, "Formato de data inválido. Use o formato DD/MM/AAAA."
        if data:
            valido, mensagem = obter_data(f"{data}")
            if valido:
                self.ids.idade_blo.error = False
                self.data_mensagem = ""
                self.data_check = True
            else:
                self.data_mensagem = "Data de nascimento inválida. " + mensagem
                self.ids.idade_blo.error = True
                self.data_check = False
        else:
            self.data_mensagem = "Data de nascimento inválida. Formato de data inválido. Use o formato DD/MM/AAAA."
            self.data_check = False

    # Função que volta para a tela de login e ativa novamente todos os botões
    def voltar(self):
        try:
            self.dialog.dismiss()
            self.dialog = None
        except:
            pass
        MDApp.get_running_app().root.get_screen('tela_login').ids.campo_usuario.disabled = False
        MDApp.get_running_app().root.get_screen('tela_login').ids.campo_senha.disabled = False
        MDApp.get_running_app().root.get_screen('tela_login').ids.botao_entrar.disabled = False
        MDApp.get_running_app().root.get_screen('tela_login').ids.botao_cadastrar.disabled = False
        save_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open_1', 'True')
        save_config_value('conf/config.ini', 'STATE', 'fechar_dialogo_adm_bloqueado', 'False')

    # Função que salva as informações de usuário do novo dispositivo e bloqueado
    def save_sql_info(self):
        global adm_existente, get_process
        self.checar_data(self.ids.idade_blo.text)
        if sql_sqlite != None:
            if self.verificar_credenciais(self.ids.usuario_adm.text, self.ids.senha_adm.text) and self.data_check == True:
                self.adm_encontrado = True
                try:
                    self.dialog.dismiss()
                    self.dialog = None
                    sql_sqlite.execute(f'''INSERT INTO seguranca (tipo_seg,
                                                                nome_blo_seg,
                                                                usuario,
                                                                senha) VALUES ('B', '{self.ids.nome_blo.text}', '{self.ids.usuario_adm.text}', '{self.ids.senha_adm.text}')''')
                    sqlite_conn.commit()
                    sql_sqlite.execute(f'''INSERT INTO bloqueados (nome_blo,
                                                                    idade_blo) VALUES ('{self.ids.nome_blo.text}', '{self.ids.idade_blo.text}')''')
                    sqlite_conn.commit()
                    get_process = True
                    # try:
                    #     # Verifica se há atividades que podem lidar com a intenção
                    #     if home_intent.resolveActivity(package_manager):
                    #         # Inicia a intenção para ir para a tela inicial
                    #         context.startActivity(home_intent)
                    #     else:
                    #         print("Não foi possível encontrar uma atividade para a tela inicial.")
                    # except:
                    #     pass
                    
                except:
                    pass
            elif len(self.ids.nome_blo.text) <= 1:
                self.start_alternative_dialog("Nome do bloqueado muito pequeno!")
                get_process = False
            elif self.data_check == False and self.data_mensagem != "":
                self.start_alternative_dialog(self.data_mensagem)
                get_process = False
            elif self.adm_encontrado == False:
                self.start_alternative_dialog("Nome de Administrador ou senha não encontrados!")
                get_process = False
    
    def start_func(self):
        self.dialog.dismiss()
        self.dialog = None
        TelaLogin().bloqueado()

    # Popup que é mostrado ao errar o usuário do adm ao adicionar o novo bloqueado no novo dispositivo
    def start_alternative_dialog(self, mensagem):
        self.dialog.dismiss()
        if self.dialog:
            self.dialog = MDDialog(
                type = "custom",
                title = "Aviso!",
                text=f"{mensagem}",
                auto_dismiss=False,
                buttons = [
                    MDRaisedButton(
                        text="Ok",
                        md_bg_color = (1,1,1,1),
                        theme_text_color = "Custom",
                        text_color = (0,0,0,1),
                        on_release = lambda x:self.start_func())
                ]
            )
        self.dialog.open()
#######################################################################################





class PermissionChecker:
    @staticmethod
    def check_package_usage_stats_permission():
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PackageManager = autoclass('android.content.pm.PackageManager')
        ApplicationInfo = autoclass('android.content.pm.ApplicationInfo')
        package_manager = PythonActivity.mActivity.getPackageManager()
        context = PythonActivity.mActivity.getApplicationContext()
        app_info = package_manager.getApplicationInfo(context.getPackageName(), PackageManager.GET_META_DATA)
        flags = app_info.flags
        return (flags & ApplicationInfo.FLAG_SYSTEM) != 0



# CLASSE DA TELA DE LOGIN
#######################################################################################
class TelaLogin(MDScreen):
    dialog = None
    tente1 = False
    tente2 = False
    switch_mostrar_senha = False

    # Função que leva o usuário as configurações para permitir a sobreposição sobre outros apps
    def abrir_configuracoes_sobreposicao(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')

        context = PythonActivity.mActivity
        intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + context.getPackageName()))
        context.startActivity(intent)

    # Função que leva o usuário as configurações para permitir que o app visualize outros apps em execução
    def abrir_configuracoes_permissao_usage_stats(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')

        context = PythonActivity.mActivity
        intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS, Uri.parse("package:" + context.getPackageName()))
        context.startActivity(intent)

    def start_check_permissions_loop(self):
        while MDApp.get_running_app():
            self.check_permissions_loop()
            time.sleep(0.1)
    
    def dialog_close_window_1(self):
        try:
            self.dialog.dismiss()
        except:
            pass
        self.dialog = None
        save_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open_1', 'True')
    
    def obter_permissao_config(self):
        # CHECA SE A PERMISSÂO FOI CONCEDIDA
        if platform == 'android':
            if read_config_value('conf/config.ini', 'PERMISSOES', 'PACKAGE_USAGE_STATS') == 'True':
                self.abrir_configuracoes_permissao_usage_stats()
                save_config_value('conf/config.ini', 'PERMISSOES', 'PACKAGE_USAGE_STATS', 'False')
                save_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open', 'False')
            if read_config_value('conf/config.ini', 'PERMISSOES', 'ACTION_MANAGE_OVERLAY_PERMISSION') == 'True':
                self.abrir_configuracoes_sobreposicao()
                save_config_value('conf/config.ini', 'PERMISSOES', 'ACTION_MANAGE_OVERLAY_PERMISSION', 'False')

    def func_1(self):
        try:
            self.dialog.dismiss()
        except:
            pass
        self.dialog = None
        save_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open_1', 'True')
        save_config_value('conf/config.ini', 'PERMISSOES', 'PACKAGE_USAGE_STATS', 'True')
        self.obter_permissao_config()
        save_config_value('conf/config.ini', 'PERMISSOES', 'ACTION_MANAGE_OVERLAY_PERMISSION', 'True')
        self.obter_permissao_config()
        save_config_value('conf/config.ini', 'STATE', 'apps_adicionados', 'True')
        

    
    def check_overlay_permission(self):
        if platform == 'android':
            # Obtenha a referência do contexto do Android
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            # Verifique se a permissão foi concedida
            overlay_permission = autoclass('android.Manifest$permission').SYSTEM_ALERT_WINDOW
            package_manager = context.getPackageManager()
            granted = package_manager.checkPermission(overlay_permission, context.getPackageName()) == autoclass('android.content.pm.PackageManager').PERMISSION_GRANTED
            return granted
        else:
            return False


    # Função que pede as permissões para o usuário
    @mainthread
    def check_permissions_loop(self):
        if sql_sqlite != None:
            if read_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open_1') == 'True':
                if read_config_value('conf/config.ini', 'STATE', 'fechar_dialogo_adm_bloqueado') == 'False':
                    sql_sqlite.execute("SELECT tipo_seg FROM seguranca")
                    resultados1 = sql_sqlite.fetchall()
                    if resultados1 == []:
                        if not self.dialog:
                            self.dialog = MDDialog(
                                title = "Alerta!",
                                type = "custom",
                                auto_dismiss=False,
                                text = "Você é um bloquado ou um administrador?",
                                buttons=[
                                    MDRaisedButton(
                                        text="Bloqueado",
                                        md_bg_color = (1,1,1,1),
                                        theme_text_color = "Custom",
                                        text_color = (0,0,0,1),
                                        on_release = lambda x: self.bloqueado()
                                    ),
                                    MDRaisedButton(
                                        text="Administrador",
                                        md_bg_color = (1,1,1,1),
                                        theme_text_color = "Custom",
                                        text_color = (0,0,0,1),
                                        on_release = lambda x: self.administrador()
                                    ),
                                ],
                            )
                        self.dialog.open()
                    for i in resultados1:
                        if i[0] == [] or i[0] == '' or i[0] == None:
                            if not self.dialog:
                                self.dialog = MDDialog(
                                    title = "Alerta!",
                                    type = "custom",
                                    auto_dismiss=False,
                                    text = "Você é um bloquado ou um administrador?",
                                    buttons=[
                                        MDRaisedButton(
                                            text="Bloqueado",
                                            md_bg_color = (1,1,1,1),
                                            theme_text_color = "Custom",
                                            text_color = (0,0,0,1),
                                            on_release = lambda x: self.bloqueado()
                                        ),
                                        MDRaisedButton(
                                            text="Administrador",
                                            md_bg_color = (1,1,1,1),
                                            theme_text_color = "Custom",
                                            text_color = (0,0,0,1),
                                            on_release = lambda x: self.administrador()
                                        ),
                                    ],
                                )
                            self.dialog.open()
                    save_config_value('conf/config.ini', 'STATE', 'fechar_dialogo_adm_bloqueado', 'True')
        #######################################################################################################
        if platform == 'android':
            if read_config_value('conf/config.ini', 'DIALOG', 'dialog_is_open_1') == "False":
                if not self.dialog:
                    self.dialog = MDDialog(
                        title = "Alerta!",
                        type = "custom",
                        auto_dismiss=False,
                        text = "CEspreita precisa da permissão de acesso a outros apps e da permissão de sobreposição a outros apps para executar corretamente!",
                        buttons=[
                            MDRaisedButton(
                                text="Não Permitir",
                                md_bg_color = (1,1,1,1),
                                theme_text_color = "Custom",
                                text_color = (0,0,0,1),
                                on_release = lambda x: self.dialog_close_window_1()
                            ),
                            MDRaisedButton(
                                text="Permitir",
                                md_bg_color = (33/255, 148/255, 243/255, 1),
                                theme_text_color = "Custom",
                                text_color = (1,1,1,1),
                                on_release = lambda x: self.func_1()
                            )
                        ],
                    )
                self.dialog.open()
    

    # Função que mostra se a permissão "PACKAGE_USAGE_STATS" foi concedida pelo usuário ou não
    def on_pre_enter(self):
        if sql_sqlite != None:
            sql_sqlite.execute("SELECT tipo_seg FROM seguranca")
            resultados = sql_sqlite.fetchall()
            for linha in resultados:
                texto = linha[0]
                if texto == "A":
                    self.ids.campo_usuario.disabled = False
                    self.ids.campo_senha.disabled = False
                    self.ids.botao_entrar.disabled = False
                    self.ids.botao_cadastrar.disabled = False
                    self.ids.esqueci_a_senha.disabled = False
                if texto == "B":
                    self.ids.campo_usuario.disabled = True
                    self.ids.campo_senha.disabled = True
                    self.ids.botao_entrar.disabled = True
                    self.ids.botao_cadastrar.disabled = True
                    self.ids.esqueci_a_senha.disabled = True
                if linha == [] or linha == '' or linha[0] == [] or linha[0] == '':
                    self.ids.campo_usuario.disabled = False
                    self.ids.campo_senha.disabled = False
                    self.ids.botao_entrar.disabled = False
                    self.ids.botao_cadastrar.disabled = False
                    self.ids.esqueci_a_senha.disabled = False
    
    




    def mostrar_senha(self):
        self.switch_mostrar_senha = not self.switch_mostrar_senha
        if self.switch_mostrar_senha:
            self.ids.campo_senha.password = True
            self.ids.show_hide_password_id.icon = 'eye-off'
        else:
            self.ids.campo_senha.password = False
            self.ids.show_hide_password_id.icon = 'eye'

    # Função que mostra o textfield na tela ao clicar para digitar, não deixa o teclado tapar ele
    def visualizar_textfield_clicar(self, textfield, focused):
        if focused:
            textfield.pos_hint = {"center_x": 0.5, "center_y": 0.46}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.84, "center_y": 0.47}
            self.ids.campo_usuario.pos_hint = {"center_x": 0.5, "center_y": 0.54}
            self.ids.account_logo.pos_hint = {"center_x": 0.845, "center_y": 0.55}
            self.ids.nome_cespreita.pos_hint = {"center_x": 0.5, "center_y": 0.68}
            self.ids.logo_cespreita.pos_hint = {"center_x": 0.5, "center_y": 0.86}
        else:
            textfield.pos_hint = {"center_x": 0.5, "center_y": 0.38}
            self.ids.show_hide_password_id.pos_hint = {"center_x": 0.84, "center_y": 0.39}
            self.ids.campo_usuario.pos_hint = {"center_x": 0.5, "center_y": 0.46}
            self.ids.nome_cespreita.pos_hint = {"center_x": 0.5, "center_y": 0.6}
            self.ids.logo_cespreita.pos_hint = {"center_x": 0.5, "center_y": 0.8}
            self.ids.account_logo.pos_hint = {"center_x": 0.845, "center_y": 0.47}

    
    def verificar_credenciais(self, usuario, senha):
        # Executar uma consulta para verificar se o usuário e senha são válidos
        sql_sqlite.execute("SELECT * FROM administrador WHERE nome_adm = ? AND senha_adm = ?", (usuario, senha))
        # Recuperar o primeiro resultado da consulta (se existir)
        resultado = sql_sqlite.fetchone()
        # Verificar se as credenciais são válidas
        if resultado:
            return True
        else:
            return False

    def login(self):
        global adm_existente, debbug_mode
        check_1 = False
        check_2 = False
        # if sql_sqlite != None:
        #     sql_sqlite.execute("SELECT * FROM administrador")
        #     info_login = sql_sqlite.fetchall()
        #     for i in info_login:
        #         usuario_adm_login = i[0]
        #         senha_adm_login = i[3]
                
        #         if self.ids.campo_usuario.text == usuario_adm_login and self.ids.campo_senha.text == senha_adm_login:
        #             sql_sqlite.execute(f"INSERT INTO seguranca (tipo_seg, usuario, senha) VALUES ('A', '{usuario_adm_login}', '{senha_adm_login}')")
        #             sqlite_conn.commit()
        #             MDApp.get_running_app().root.transition = RiseInTransition()
        #             MDApp.get_running_app().root.current = "tela_principal"
        #             adm_existente = f"{usuario_adm_login}"
        if sql_sqlite != None:
            sql_sqlite.execute("SELECT * FROM administrador")
            info_login = sql_sqlite.fetchall()
            for i in info_login:
                usuario_adm_login = i[0]
                senha_adm_login = i[3]

                if debbug_mode:
                    self.ids.campo_usuario.text = f'{usuario_adm_login}'
                    self.ids.campo_senha.text = f'{senha_adm_login}'

            if self.verificar_credenciais(self.ids.campo_usuario.text, self.ids.campo_senha.text):
                if sql_sqlite != None:
                    
                    MDApp.get_running_app().root.transition = RiseInTransition()
                    MDApp.get_running_app().root.current = "tela_principal"
                    adm_existente = f"{usuario_adm_login}"

                    sql_sqlite.execute("SELECT tipo_seg FROM seguranca")
                    resultados = sql_sqlite.fetchall()
                    for linha in resultados:
                        texto = linha[0]
                        if texto == "A":
                            self.ids.campo_usuario.disabled = False
                            self.ids.campo_senha.disabled = False
                            self.ids.botao_entrar.disabled = False
                            self.ids.botao_cadastrar.disabled = False
                            self.ids.esqueci_a_senha.disabled = False
                            
                            MDApp.get_running_app().root.transition = RiseInTransition()
                            MDApp.get_running_app().root.current = "tela_principal"
                            adm_existente = f"{self.ids.campo_usuario.text}"
                        if texto == "B":
                            self.ids.campo_usuario.disabled = True
                            self.ids.campo_senha.disabled = True
                            self.ids.botao_entrar.disabled = True
                            self.ids.botao_cadastrar.disabled = True
                            self.ids.esqueci_a_senha.disabled = True
                        if linha == [] or linha == '' or linha[0] == [] or linha[0] == '':
                            self.ids.campo_usuario.disabled = False
                            self.ids.campo_senha.disabled = False
                            self.ids.botao_entrar.disabled = False
                            self.ids.botao_cadastrar.disabled = False
                            self.ids.esqueci_a_senha.disabled = False
                    try:
                        self.dialog.dismiss()
                        self.dialog = None
                    except:
                        pass
                    if sql_sqlite != None:
                        sql_sqlite.execute("SELECT usuario FROM seguranca")
                        resultados2 = sql_sqlite.fetchall()
                        for linha in resultados2:
                            texto = linha[0]
                            if texto == None:
                                self.tente1 = True
                        
                        sql_sqlite.execute("SELECT senha FROM seguranca")
                        resultados3 = sql_sqlite.fetchall()
                        for linha in resultados3:
                            texto = linha[0]
                            if texto == None:
                                self.tente2 = True



                sql_sqlite.execute("SELECT * FROM seguranca")
                seguranca_dados = sql_sqlite.fetchall()
                for a in seguranca_dados:
                    status_ce = a[0] # Verifica se é B(bloqueado) ou A(administrador)
                    if status_ce == "A":
                        # Muda para a tela principal
                        MDApp.get_running_app().root.transition = RiseInTransition()
                        MDApp.get_running_app().root.current = "tela_principal"
                        adm_existente = f"{usuario_adm_login}"
            else:
                try:
                    self.dialog.dismiss()
                    self.dialog = None
                except:
                    pass
                if not self.dialog:
                    self.dialog = MDDialog(
                        title = "Aviso!",
                        text = "Usuário ou senha incorretos, verifique as informções e tente novamente!",
                        buttons = [
                            MDRaisedButton(text = "Ok",
                                            md_bg_color = (1,1,1,1),
                                            theme_text_color = "Custom",
                                            text_color = (0,0,0,1),
                                            on_release = lambda x:self.dialog.dismiss())
                        ]
                    )
                self.dialog.open()
    
    def dialog_dismiss(self):
        try:
            self.dialog.dismiss()
            self.dialog = None
        except:
            pass

    
    def administrador(self):
        global adm_existente
        try:
            if sql_sqlite != None:
                sql_sqlite.execute(f"INSERT INTO seguranca (tipo_seg, usuario, senha) VALUES ('A', '', '')")
                sqlite_conn.commit()
        except:
            pass
        self.dialog_dismiss()
        self.ids.campo_usuario.disabled = False
        self.ids.campo_senha.disabled = False
        self.ids.botao_entrar.disabled = False
        self.ids.botao_cadastrar.disabled = False
        self.ids.esqueci_a_senha.disabled = False
    

    def bloqueado(self):
        MDApp.get_running_app().root.current = "tela_login"
        self.ids.campo_usuario.disabled = True
        self.ids.campo_senha.disabled = True
        self.ids.botao_entrar.disabled = True
        self.ids.botao_cadastrar.disabled = True
        self.ids.esqueci_a_senha.disabled = True
        try:
            self.dialog_dismiss()
        except:
            pass
        Info_bloqueado().open_dialog()
#######################################################################################