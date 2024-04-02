# IMPORTANDO KIVY
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.screenmanager import SlideTransition
from kivy.utils import platform
# import psycopg2
import sqlite3
# import psutil
import threading
import time
from kivy.clock import Clock, mainthread
import configparser

# IMPORTANDO TELAS
from pyFiles import tela_cadastro
from pyFiles import tela_alerta
from pyFiles import tela_principal
from pyFiles import tela_cadBloqueados
from pyFiles import tela_login
from pyFiles import tela_lista_apps
from pyFiles import tela_sitesBloq
from pyFiles import Tela_opcoes_principais


####################################---VÁRIAVEIS---####################################
id_adm                = 1

bloqueado_selecionado = "" # Váriavel de controle do bloqueado

# Variaveis que executam comandos sql
sql_postgre           = None
sql_sqlite            = None

# Variaveis que configuram o sql
sqlite_conn           = None
postgre_conn          = None

lista_de_processos_pc = []
#######################################################################################


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



if platform == 'win':
    Window.size = (350, 650)
    tela_login.debbug_mode = True
    tela_cadastro.debbug_mode = True
    save_config_value('conf/config.ini', 'PERMISSOES', 'package_usage_stats', 'False')
    save_config_value('conf/config.ini', 'PERMISSOES', 'action_manage_overlay_permission', 'False')
if platform == 'linux':
    Window.size = (350, 650)
    tela_login.debbug_mode = True
    tela_cadastro.debbug_mode = True
    save_config_value('conf/config.ini', 'PERMISSOES', 'package_usage_stats', 'False')
    save_config_value('conf/config.ini', 'PERMISSOES', 'action_manage_overlay_permission', 'False')




# CLASSE DA TELA "TELA"
#######################################################################################
class TelaTela(MDScreen):
    def menu_open(self):
        menu_items = [
            {
                "text": f"Tela",
                "viewclass": "OneLineListItem",
                "on_release": lambda:print(),
            }
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.button_show_menu,
            items=menu_items,
            width_mult=4,
            position="bottom",
        )
        self.menu.bind()
        self.menu.open()
#######################################################################################



# Função responsável por voltar para o inicio no android
#######################################################################################
def voltar_inicio():
    try:
        from jnius import autoclass
        # Obtém referências para as classes necessárias
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        PackageManager = autoclass('android.content.pm.PackageManager')

        # Obtém o contexto atual
        context = PythonActivity.mActivity

        # Cria um intent para a tela inicial
        home_intent = Intent(Intent.ACTION_MAIN)
        home_intent.addCategory(Intent.CATEGORY_HOME)

        # Obtém o PackageManager para verificar se a intenção pode ser resolvida
        package_manager = context.getPackageManager()
        
        if home_intent.resolveActivity(package_manager):
            # Inicia a intenção para ir para a tela inicial
            context.startActivity(home_intent)
        else:
            print("Não foi possível encontrar uma atividade para a tela inicial.")
    except:
        pass
#######################################################################################

    

#######################################################################################
class ScreenManagement(MDScreenManager):
    pass
#######################################################################################



# ----- CLASSE PRINCIPAL DO APLICATIVO ----- #
#######################################################################################
class CEspreita(MDApp):
    dialog = None
    administrador_logado = ""
    
    def connect(self):
        global sql_postgre, postgre_conn, sql_sqlite, sqlite_conn, id_adm
        # --- POSTREE --- #
        try:
            # ----- POSTGRE DESABILITADO TEMPORARIAMENTE ATÉ O LANÇAMENTO DO APLICATIVO ----- #
            postgre_conn = None
            sql_postgre = None
        except Exception as e:
            postgre_conn = None
            sql_postgre = None
            print(e)
        
        try:
            sql_postgre.execute("SELECT max(id_adm) FROM ADMINISTRADOR WHERE id_adm > 0")
            # Recupere o resultado usando fetchone()
            resultado = sql_postgre.fetchone()
            # Verifique se a consulta retornou resultados
            if resultado is not None:
                # O valor id_adm está na primeira coluna do resultado
                id_adm = resultado[0]
                if id_adm == None:
                    id_adm = 0
                tela_cadastro.id_adm      = id_adm
                # tela_cadBloqueados.id_adm = id_adm
                # Imprima o valor id_adm
                print("ID do administrador:", id_adm)
            else:
                # A consulta não retornou resultados
                print("Nenhum administrador encontrado")
            #-----------------#
        except:
            pass
        
        
        try:
            # --- SQLITE --- #
            sqlite_conn = sqlite3.connect('administrador.db')
            sql_sqlite = sqlite_conn.cursor()
            sqlite_conn.commit()

            
            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS administrador (
                        nome_adm TEXT,
                        cpf_cnpj_adm TEXT,
                        data_nascimento_adm DATE,
                        senha_adm TEXT,
                        numero_telefone_adm TEXT,
                        email_adm TEXT,
                        id_adm INTEGER PRIMARY KEY
                    );
                ''')
            sqlite_conn.commit()
            
            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS aplic_bloc (
                        codigo_apl TEXT,
                        nome_apl TEXT,
                        tip_bloq_apl TEXT,
                        bloc_horario_unico TEXT,
                        ap_hor1_apl TEXT,
                        ap_hor2_apl TEXT,
                        ap_hor3_apl TEXT,
                        ap_hor4_apl TEXT,
                        at_hor1_apl TEXT,
                        at_hor2_apl TEXT,
                        at_hor3_apl TEXT,
                        at_hor4_apl TEXT
                    );
                ''')
            sqlite_conn.commit()
            
            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS bloqueados (
                        nome_blo TEXT,
                        idade_blo TEXT
                    );
                ''')
            sqlite_conn.commit()
            
            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS listaapps (
                        nome_apps TEXT,
                        nome_adm TEXT,
                        nome_blo TEXT
                    );
                ''')
            sqlite_conn.commit()
            
            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS listasites (
                        nome_sites TEXT,
                        url_sites TEXT,
                        nome_adm TEXT,
                        nome_blo TEXT
                    );
                ''')
            sqlite_conn.commit()

            sql_sqlite.execute('''
                    CREATE TABLE IF NOT EXISTS seguranca (
                        tipo_seg TEXT,
                        nome_blo_seg TEXT,
                        usuario TEXT,
                        senha TEXT
                    );
                ''')
            sqlite_conn.commit()
            
            sql_sqlite.execute("CREATE TABLE IF NOT EXISTS usuarios_selecionados (bloqueados_ativos TEXT);")
            sqlite_conn.commit()
        except:
            pass
        

        try:
            # ADICIONAR OS COMANDOS SQL EM OUTROS ARQUIVOS .PY
            tela_cadastro.postgre_conn = postgre_conn
            tela_cadastro.sql_postgre = sql_postgre
            tela_cadastro.sqlite_conn = sqlite_conn
            tela_cadastro.sql_sqlite = sql_sqlite

            tela_cadBloqueados.postgre_conn = postgre_conn
            tela_cadBloqueados.sql_postgre = sql_postgre
            tela_cadBloqueados.sqlite_conn = sqlite_conn
            tela_cadBloqueados.sql_sqlite = sql_sqlite
            
            tela_principal.sql_sqlite = sql_sqlite
            tela_principal.sqlite_conn = sqlite_conn
            tela_principal.sql_postgre = sql_postgre
            tela_principal.postgre_conn = postgre_conn

            tela_lista_apps.sql_sqlite = sql_sqlite
            tela_lista_apps.sqlite_conn = sqlite_conn
            tela_lista_apps.sql_postgre = sql_postgre
            tela_lista_apps.postgre_conn = postgre_conn
            
            tela_sitesBloq.sql_sqlite = sql_sqlite
            tela_sitesBloq.sqlite_conn = sqlite_conn
            tela_sitesBloq.sql_postgre = sql_postgre
            tela_sitesBloq.postgre_conn = postgre_conn
             
            Tela_opcoes_principais.sql_sqlite = sql_sqlite
            Tela_opcoes_principais.sqlite_conn = sqlite_conn
            Tela_opcoes_principais.sql_postgre = sql_postgre
            Tela_opcoes_principais.postgre_conn = postgre_conn

            
            tela_login.sql_sqlite = sql_sqlite
            tela_login.sqlite_conn = sqlite_conn
            tela_login.sql_postgre = sql_postgre
            tela_login.postgre_conn = postgre_conn
        except:
            tela_cadastro.postgre_conn = None
            tela_cadastro.sql_postgre = None
            tela_cadastro.sqlite_conn = None
            tela_cadastro.sql_sqlite = None

            tela_cadBloqueados.postgre_conn = None
            tela_cadBloqueados.sql_postgre = None
            tela_cadBloqueados.sqlite_conn = None
            tela_cadBloqueados.sql_sqlite = None

            tela_principal.sql_postgre = None
            tela_principal.postgre_conn = None
            tela_principal.sql_sqlite = None
            tela_principal.sqlite_conn = None
            
            tela_lista_apps.sql_sqlite = None
            tela_lista_apps.sqlite_conn = None
            tela_lista_apps.sql_postgre = None
            tela_lista_apps.postgre_conn = None
            
            tela_sitesBloq.sql_sqlite = None
            tela_sitesBloq.sqlite_conn = None
            tela_sitesBloq.sql_postgre = None
            tela_sitesBloq.postgre_conn = None
            
            Tela_opcoes_principais.sql_sqlite = None
            Tela_opcoes_principais.sqlite_conn = None
            Tela_opcoes_principais.sql_postgre = None
            Tela_opcoes_principais.postgre_conn = None
            
            tela_login.sql_sqlite = None
            tela_login.sqlite_conn = None
            tela_login.sql_postgre = None
            tela_login.postgre_conn = None

        print("\n\n# --- BANCO DE DADOS LOCAL CRIADO E CONECTADO SQLITE--- #\n\n")
        #-----------------#

    def start_thread_check_adm(self):
        while MDApp.get_running_app():
            time.sleep(0.5)
            self.adicionar_administrador_existente()
    
    @mainthread
    def adicionar_administrador_existente(self):
        if tela_login.adm_existente != "":
            tela_alerta.user_adm_logado = tela_login.adm_existente
            tela_cadastro.user_adm_logado = tela_login.adm_existente
            tela_cadBloqueados.user_adm_logado = tela_login.adm_existente
            tela_lista_apps.user_adm_logado = tela_login.adm_existente
            Tela_opcoes_principais.user_adm_logado = tela_login.adm_existente
            tela_principal.user_adm_logado = tela_login.adm_existente
            tela_sitesBloq.user_adm_logado = tela_login.adm_existente
        else:
            tela_alerta.user_adm_logado = None
            tela_cadastro.user_adm_logado = None
            tela_cadBloqueados.user_adm_logado = None
            tela_lista_apps.user_adm_logado = None
            Tela_opcoes_principais.user_adm_logado = None
            tela_principal.user_adm_logado = None
            tela_sitesBloq.user_adm_logado = None
    

    def get_pc_process(self):
        global lista_de_processos_pc
        try:
            if sql_sqlite != None:
                # Obtem o tipo de usuário no dispositivo atual, se ele é B(bloqueado) ou A(administrador)
                # Obtem o adm que controla o bloqueado atual
                sql_sqlite.execute("SELECT * FROM seguranca")
                seguranca_dados = sql_sqlite.fetchall()
                for a in seguranca_dados:
                    status_ce = a[0] # Verifica se é B(bloqueado) ou A(administrador)
                    usr_bloqueado = a[1] # Obtem dades que podem lidar com a intenção
                    # TEMPORARIO o nome do bloqueado
                    adm = a[2] # Obtem o nome do administrador do respectivo bloqueado

                    if status_ce == "B": # TEM QUE SER (B) PARA EXECUTAR AS AÇÕES ABAIXO
                        try:
                            voltar_inicio()
                        except:
                            pass
                
                        # Obtem a lista de aplicativos do bloqueado no dispositivo atual e adiciona no banco de dados com os identificadores de nome do bloqueado e nome do administrador
                        # for processo in psutil.process_iter(['pid', 'name', 'username']):
                        #     if processo.info['name'] != '' and processo.info['name'] != None:
                        #         lista_de_processos_pc.append(processo.info['name'])
                        #         sql_sqlite.execute(f"INSERT INTO listaapps (nome_apps, nome_adm, nome_blo) VALUES ('{processo.info['name']}', '{adm}', '{usr_bloqueado}')")
                        #         sqlite_conn.commit()
        except:
            pass
    





    def on_start(self):
        global bloqueado_selecionado
        self.connect()

        self.get_pc_process()
        
        threading.Thread(target=self.start_thread_check_adm).start()


        save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start", "False")
        threading.Thread(target=tela_lista_apps.TelaApp_config().start_thread_bloq_apps).start()
        
        threading.Thread(target=tela_login.TelaLogin().start_check_permissions_loop).start()
        tela_sitesBloq.TelaSites_Bloq().obter_dados()

        save_config_value('conf/config.ini', 'STATE', 'APPS_INSTALADOS_OBTIDOS', 'False')

        if sql_sqlite:
            sql_sqlite.execute("SELECT tipo_seg FROM seguranca")
            resultados = sql_sqlite.fetchall()
            for linha in resultados:
                if linha == [] or linha == '' or linha[0] == [] or linha[0] == '':
                    save_config_value('conf/config.ini', 'STATE', 'fechar_dialogo_adm_bloqueado', 'False')
            save_config_value('conf/config.ini', 'STATE', 'fechar_dialogo_adm_bloqueado', 'False')
        
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            request_permissions([Permission.ACCESS_BACKGROUND_LOCATION])
            request_permissions([Permission.ACCESS_FINE_LOCATION])
            request_permissions([Permission.BATTERY_STATS])
            request_permissions([Permission.CAMERA])
            request_permissions([Permission.POST_NOTIFICATIONS])
            try:
                # Inicia o serviço em segundo plano
                from jnius import autoclass
                PythonService = autoclass('org.kivy.android.PythonService')
                service = autoclass('cecotein.informatica.cespreitaapp.informatica.ServiceMyservice')
                mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                argument = ''
                service.start(mActivity, argument)
                PythonService.mService.setAutoRestartService(True)
            except:
                pass

    
    def on_pause(self):
        try:
            # Inicia o serviço em segundo plano
            from jnius import autoclass
            PythonService = autoclass('org.kivy.android.PythonService')
            service = autoclass('cecotein.informatica.cespreitaapp.informatica.ServiceMyservice')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            argument = ''
            service.start(mActivity, argument)
            PythonService.mService.setAutoRestartService(True)
        except:
            pass
        return True

    def voltar(self):
        self.root.transition = SlideTransition()
        self.root.transition.direction = "down"
        self.root.current = "tela_principal"

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_file("kvFiles/main.kv")
#######################################################################################



CEspreita().run()

try:
    if sqlite_conn != None:
        sqlite_conn.close()
    if postgre_conn != None:
        postgre_conn.close()
except:
    pass