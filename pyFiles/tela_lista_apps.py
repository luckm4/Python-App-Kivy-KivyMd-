from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton
from kivymd.app import MDApp
from kivy.uix.screenmanager import NoTransition, SlideTransition
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import mainthread, Clock
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconLeftWidget, IconRightWidget
from kivy.utils import platform
import configparser
import threading
import time
from datetime import datetime
# import psutil
# import os

if platform == 'android':
    from jnius import autoclass

####################################---VÁRIAVEIS---####################################
lista_apps                = [] # Lista que armazena os apps a serem bloqueados
select_apps               = [] # Lista que armazena os apps a serem bloqueados que estão selecionados
apps_deletados            = [] # Lista que armazena os apps a serem deletados
lista_apps_mostrados      = [] # Lista que armazena os apps que ja estão sendo mostrados ao usuário, assim não repetindo os mesmos apps
lista_apps_no_dispositivo = None # Lista que armazena os apps que já estão instalados no dispositivo atual
item_widgets              = {} # Dicionário contendo todos os widgets adicionados a lista de apps

id_button                 = None # Variavel de controle para o id de um botão, não mexer
section_name              = None # Variavel de controle para indicar a seção a ser modificada no arquivo config.ini, não mexer

# Variaveis que executam comandos sql
sql_postgre               = None
sql_sqlite                = None

# Variaveis que configuram o sql
postgre_conn              = None
sqlite_conn               = None

switch_check_text         = False # Váriavel de controle de UIX

user_adm_logado           = None # Váriavel de controle de adm
bloqueado_selecionado     = "" # Váriavel de controle do bloqueado

app_recem_adicionado      = "" # Váriavel que verifica se o app foi adicionado neste instante para aplicar o status de "BLOQUEADO_INDETERMINADO"

cb_1                      = False # Controle da checkbox Bloqueado da tela de configuração de apps bloqueados, identifica se o checkbox está ativado ou desativado
cb_2                      = False # Controle da checkbox Horas de uso da tela de configuração de apps bloqueados, identifica se o checkbox está ativado ou desativado
cb_3                      = False # Controle da checkbox Bloquear por horário da tela de configuração de apps bloqueados, identifica se o checkbox está ativado ou desativado
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



# Função para remover todas as opções de um arquivo ini
#########################################################################################################
def remove_all_options_in_section(file_path, section_name):
    try:
        # Crie um objeto ConfigParser
        config = configparser.ConfigParser()
        # Leia o arquivo INI
        config.read(file_path)
        # Verifique se a seção existe
        if config.has_section(section_name):
            # Obtenha a lista de variáveis na seção
            variables_to_remove = config.options(section_name)
            # Remova cada variável da seção
            for variable in variables_to_remove:
                config.remove_option(section_name, variable)
            # Abra o arquivo INI no modo de gravação para atualizá-lo
            with open(file_path, 'w') as configfile:
                config.write(configfile)
            return True  # Remoção bem-sucedida
        else:
            return False  # A seção não existe
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return False  # Ocorreu um erro

def remover_item_ini(arquivo_ini, secao, chave):
    config = configparser.ConfigParser()
    config.read(arquivo_ini)
    if config.has_section(secao) and config.has_option(secao, chave):
        config.remove_option(secao, chave)
        with open(arquivo_ini, 'w') as arquivo:
            config.write(arquivo)
    else:
        pass
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



#########################################################################################################
def verificar_e_atualizar(nome_apl, novo_valor):
    # Consulta SQL SELECT para verificar se o nome_apl está preenchido com o nome que procuramos
    sql_select = "SELECT COUNT(*) FROM aplic_bloc WHERE nome_apl = ?"
    sql_sqlite.execute(sql_select, (nome_apl,))
    resultado = sql_sqlite.fetchone()[0]
    # Se o nome_apl estiver preenchido com o nome que procuramos, atualize o valor de tip_bloq_apl
    if resultado > 0:
        # Instrução SQL UPDATE para atualizar o valor de tip_bloq_apl
        sql_update = "UPDATE aplic_bloc SET tip_bloq_apl = ? WHERE nome_apl = ?"
        sql_sqlite.execute(sql_update, (novo_valor, nome_apl))
        sqlite_conn.commit()
        # print("O valor de tip_bloq_apl foi atualizado com sucesso.")
    else:
        # print("O nome_apl não está preenchido com o nome que procuramos.")
        pass
    sqlite_conn.commit()
#########################################################################################################










# Classe do widget de carregamento
#########################################################################################################
class Carregamento(MDScreen):
    pass
#########################################################################################################











# Classe de cada item que será criado na lista, exemplo: o item "aplicativo 1", "aplicativo 2" etc
#########################################################################################################
class ListaApps(MDCard):
    global item_widgets
    icon_btn_switch = False
    item_lista = None
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cria o item que será adicionado na lista
        self.item_lista = OneLineAvatarIconListItem(
                IconLeftWidget(
                    icon="android",
                ),
                IconRightWidget(
                    theme_text_color = "Custom",
                    icon_color = (1,0,0,1),
                    icon="trash-can-outline",
                    on_release = lambda x:self.delete_app(text)
                ),
                IconRightWidget(
                    icon="dots-vertical",
                    on_release = lambda x:self.mudar_janela('apps_config', text)
                ),
                theme_text_color = "Custom",
                text_color = (1,0,0,1),
                text=f"{text}",
            )
        item_widgets[text] = self.item_lista
        # Adicionando o item à lista
        threading.Thread(target=self.add_thread).start() # Thread que inicia a criação do item
    # Função que chama a thread padrão do kivy e converte a thread do python para não dar erro
    def add_thread(self):
        Clock.schedule_once(self.add)
    # Função que adiciona os itens a lista utilizando a thread do kivy
    def add(self, *args):
        MDApp.get_running_app().root.get_screen('tela_lista_apps').ids.app_list.add_widget(self.item_lista)
    # Função que muda a janela que o usuário está ao clicar nos três pontos para configurar o aplicativo bloqueado
    def mudar_janela(self, tela, text):
        global section_name
        section_name = text
        MDApp.get_running_app().root.transition = NoTransition()
        MDApp.get_running_app().root.current = tela
    # FUNÇÃO RESPONSAVEL POR DELETAR OS ITENS DA LISTA PRINCIPAL ONDE MOSTRAM APENAS ITENS SELECIONADOS PELO USUÁRIO
    def delete_app(self, texto):
        global apps_deletados
        # DELETA O ITEM ATUAL DA LISTA DE APPS MOSTRADOS NA TELA
        if self.item_lista != None:
            for item in MDApp.get_running_app().root.get_screen('tela_lista_apps').ids.app_list.children:
                MDApp.get_running_app().root.get_screen('tela_lista_apps').ids.app_list.remove_widget(self.item_lista)
                break
        # ADICIONA O APP A LISTA DE APPS DELETADOS
        apps_deletados.append(f'{texto}')
        # ITERA SOBRE A LISTA DE APPS DELETADOS
        for i in apps_deletados:
            try:
                # DELETA O APP DAS TABELAS "listaapps" e "aplic_bloc" DO SQL
                sql_sqlite.execute(f"DELETE FROM listaapps WHERE nome_apps = '{i}';")
                sql_sqlite.execute(f"DELETE FROM aplic_bloc WHERE nome_apl = '{i}';")
                remove_all_options_in_section("conf/lista_apps_config.ini", f"{i}")
                remover_item_ini("conf/lista_apps_config.ini", "CHECKBOXES", f"{i} 1")
                remover_item_ini("conf/lista_apps_config.ini", "CHECKBOXES", f"{i} 2")
                remover_item_ini("conf/lista_apps_config.ini", "CHECKBOXES", f"{i} 3")
                sqlite_conn.commit()
            except:
                pass
   
#########################################################################################################







# Content que contém os horários de bloqueio
#########################################################################################################
class Content(MDBoxLayout):
    def __init__(self, text1, text2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.text_field_1.text = f'{text1}'
        self.ids.text_field_2.text = f'{text2}'
    
    # def define_limit_value_hora(self, textfield_id):
    #     hora_atual = datetime.now()
    #     hora_atual_formatada = hora_atual.strftime("%H")
    #     self.limit_value(textfield_id, int(hora_atual_formatada))
    # def define_limit_value_minuto(self, textfield_id):
    #     hora_atual = datetime.now()
    #     minuto_atual_formatado = hora_atual.strftime("%M")
    #     self.limit_value(textfield_id, int(minuto_atual_formatado))

    def limit_value(self, text_field, max_value):
        global id_button, section_name
        # btn1 é uma referência ao botão de bloquear por hora
        if id_button != None and id_button == "btn1":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn1.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn1", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        # btn2 e btn3 são os dois primeiros botões da parte de bloquear por horário marcado de um inicio a um fim
        if id_button != None and id_button == "btn2":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn2.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn2", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        if id_button != None and id_button == "btn3":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn3.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn3", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
            
        # btn4 e btn5 são os botões do segundo horário de bloquear por horário marcado de um inicio a um fim
        if id_button != None and id_button == "btn4":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn4.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn4", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        if id_button != None and id_button == "btn5":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn5.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn5", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        # btn6 e btn7 são os botões do terceiro horário de bloquear por horário marcado de um inicio a um fim
        if id_button != None and id_button == "btn6":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn6.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn6", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        if id_button != None and id_button == "btn7":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn7.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn7", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        # btn8 e btn9 são os botões do quarto horário de bloquear por horário marcado de um inicio a um fim
        if id_button != None and id_button == "btn8":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn8.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn8", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        if id_button != None and id_button == "btn9":
            MDApp.get_running_app().root.get_screen('apps_config').ids.btn9.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            save_config_value("conf/lista_apps_config.ini", f"{section_name}", "btn9", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        try:
            value = int(text_field.text)
            if value > max_value:
                text_field.text = str(max_value)
            if len(text_field.text) > 2:
                text_field.text = str("")
        except ValueError:
            text_field.text = ''
#########################################################################################################





# Tela de configurações do item atual
#########################################################################################################
class TelaApp_config(MDScreen):
    dialog = None
    check_1 = False
    check_2 = False
    check_3 = False
    nomes_apps = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # Função responsável por iniciar os threads da tela
    def start_thread_bloq_apps(self):
        while MDApp.get_running_app():
            time.sleep(1)
            self.check_sql()
    
    # Essa função serve para identificar qual checkbox está ativo e atribuir sua função a lista de apps no banco de dados sql
    @mainthread
    def check_sql(self):
        global cb_1, cb_2, cb_3
        if read_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start") == "False":
            if sql_sqlite:
                sql_sqlite.execute("SELECT nome_apps FROM listaapps")
                self.nomes_apps = sql_sqlite.fetchall()
                save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start", "True")
                
        if self.nomes_apps:
            for a in self.nomes_apps:
                check_checkbox_1 = read_config_value("conf/lista_apps_config.ini", "CHECKBOXES", "{0}".format(f"{a[0]} 1"))
                check_checkbox_2 = read_config_value("conf/lista_apps_config.ini", "CHECKBOXES", "{0}".format(f"{a[0]} 2"))
                check_checkbox_3 = read_config_value("conf/lista_apps_config.ini", "CHECKBOXES", "{0}".format(f"{a[0]} 3"))
                if check_checkbox_1 == "False" and check_checkbox_2 == "False" and check_checkbox_3 == "False":
                    verificar_e_atualizar(a[0], "DESBLOQUEADO")

                if check_checkbox_1 == "True" and check_checkbox_2 == "False" and check_checkbox_3 == "False":
                    verificar_e_atualizar(a[0], "BLOQUEADO_INDETERMINADO")

                if check_checkbox_1 == "False" and check_checkbox_2 == "True" and check_checkbox_3 == "False":
                    verificar_e_atualizar(a[0], "HORAS_DE_USO")

                if check_checkbox_1 == "False" and check_checkbox_2 == "False" and check_checkbox_3 == "True":
                    verificar_e_atualizar(a[0], "LIBERAR_POR_HORARIO")
                    
    
    # Controla os checkboxes e suar ações
    def checkbox_group(self, checkbox):
        global cb_1, cb_2, cb_3
        cont = 0
        checkboxes = [self.ids.check_1, self.ids.check_2, self.ids.check_3]
        sql_sqlite.execute("SELECT nome_apps FROM listaapps")
        nomes_apps = sql_sqlite.fetchall()
        for i in nomes_apps:
            if section_name in i[0]:
                for cb in checkboxes:
                    cont = cont + 1
                    if cont < 1:
                        cont = 1
                    if cont >= 3:
                        cont = 3
                    if cb == checkbox:
                        # cb.active = True # remover o comentário desta linha faz com que sempre tenha pelo menos 1 checkbox ativo, nenhum poderá ser desativado!
                        save_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}", "True")
                        if cont == 1:
                            cb_1 = True
                            save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start", "False")
                            if cb.active == False:
                                save_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}", "False")
                        else:
                            cb_1 = False
                        
                        if cont == 2:
                            cb_2 = True
                            save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start", "False")
                            if cb.active == False:
                                save_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}", "False")
                        else:
                            cb_2 = False

                        if cont == 3:
                            cb_3 = True
                            save_config_value("conf/lista_apps_config.ini", "SQL_THREAD", "thread_sql_start", "False")
                            if cb.active == False:
                                save_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}", "False")
                        else:
                            cb_3 = False
                        
                        if cont == 1 and cb.active == False:
                            cb_1, cb_2, cb_3 = False, False, False
                        if cont == 2 and cb.active == False:
                            cb_1, cb_2, cb_3 = False, False, False
                        if cont == 3 and cb.active == False:
                            cb_1, cb_2, cb_3 = False, False, False
                        if cont < 1 or cont > 3:
                            cb_1, cb_2, cb_3 = False, False, False
                    else:
                        cb.active = False
                        save_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}", "False")
                    
                    
    # Função padrão do kivy para executar uma ação ao entrar em uma tela
    def on_enter(self):
        self.update_buttons_states(section_name)
        self.get_checkbox_state()
    
    # Obtem o estado do checkbox pelo arquivo "conf/lista_apps_config.ini" e adiciona seu estado definido no arquivo ao checkbox
    def get_checkbox_state(self):
        for cont in range(1, 4):
            # # Salva o estado dos checkbox que foram pré definidos por padrão antes da tela obter seus estados e aplicar aos checkbox
            if not read_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{section_name} 1'):
                save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{section_name} 1', 'True') # Ativa a primeira opção por padrão ao criar o app
                save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{section_name} 2', 'False')
                save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{section_name} 3', 'False')

            # Obtém os estados dos checkboxes salvos e aplica aos checkboxes da tela
            checkbox = read_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{section_name} {cont}")
            if cont == 1:
                if checkbox == "True":
                    self.ids.check_1.active = True
                else:
                    self.ids.check_1.active = False
            if cont == 2:
                if checkbox == "True":
                    self.ids.check_2.active = True
                else:
                    self.ids.check_2.active = False
            if cont == 3:
                if checkbox == "True":
                    self.ids.check_3.active = True
                else:
                    self.ids.check_3.active = False

    def voltar(self):
        MDApp.get_running_app().root.transition.direction = "right"
        MDApp.get_running_app().root.current = "tela_lista_apps"
        TelaListaApps().remove_loading()

    def update_buttons_states(self, section):
        sql_sqlite.execute("SELECT nome_apps FROM listaapps")
        nomes_apps = sql_sqlite.fetchall()
        for i in nomes_apps:
            if section in i[0]:
                btn1 = read_config_value("conf/lista_apps_config.ini", section, f"btn1")
                btn2 = read_config_value("conf/lista_apps_config.ini", section, f"btn2")
                btn3 = read_config_value("conf/lista_apps_config.ini", section, f"btn3")
                btn4 = read_config_value("conf/lista_apps_config.ini", section, f"btn4")
                btn5 = read_config_value("conf/lista_apps_config.ini", section, f"btn5")
                btn6 = read_config_value("conf/lista_apps_config.ini", section, f"btn6")
                btn7 = read_config_value("conf/lista_apps_config.ini", section, f"btn7")
                btn8 = read_config_value("conf/lista_apps_config.ini", section, f"btn8")
                btn9 = read_config_value("conf/lista_apps_config.ini", section, f"btn9")

                self.ids.btn1.text = f"{btn1}"
                self.ids.btn2.text = f"{btn2}"
                self.ids.btn3.text = f"{btn3}"
                self.ids.btn4.text = f"{btn4}"
                self.ids.btn5.text = f"{btn5}"
                self.ids.btn6.text = f"{btn6}"
                self.ids.btn7.text = f"{btn7}"
                self.ids.btn8.text = f"{btn8}"
                self.ids.btn9.text = f"{btn9}"
                
                if btn1 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn1", f"09:00")
                    btn1 = read_config_value("conf/lista_apps_config.ini", section, f"btn1")
                    self.ids.btn1.text = f"{btn1}"
                if btn2 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn2", f"07:00")
                    btn2 = read_config_value("conf/lista_apps_config.ini", section, f"btn2")
                    self.ids.btn2.text = f"{btn2}"
                if btn3 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn3", f"08:00")
                    btn3 = read_config_value("conf/lista_apps_config.ini", section, f"btn3")
                    self.ids.btn3.text = f"{btn3}"
                if btn4 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn4", f"09:00")
                    btn4 = read_config_value("conf/lista_apps_config.ini", section, f"btn4")
                    self.ids.btn4.text = f"{btn4}"
                if btn5 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn5", f"10:00")
                    btn5 = read_config_value("conf/lista_apps_config.ini", section, f"btn5")
                    self.ids.btn5.text = f"{btn5}"
                if btn6 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn6", f"11:00")
                    btn6 = read_config_value("conf/lista_apps_config.ini", section, f"btn6")
                    self.ids.btn6.text = f"{btn6}"
                if btn7 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn7", f"12:00")
                    btn7 = read_config_value("conf/lista_apps_config.ini", section, f"btn7")
                    self.ids.btn7.text = f"{btn7}"
                if btn8 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn8", f"13:00")
                    btn8 = read_config_value("conf/lista_apps_config.ini", section, f"btn8")
                    self.ids.btn8.text = f"{btn8}"
                if btn9 == None:
                    save_config_value("conf/lista_apps_config.ini", f"{section}", "btn9", f"14:00")
                    btn9 = read_config_value("conf/lista_apps_config.ini", section, f"btn9")
                    self.ids.btn9.text = f"{btn9}"

    def setar_hora(self, id):
        global id_button
        id_button = id
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Horas de uso",
                type = "custom",
                content_cls = Content(self.ids[id_button].text[0:2], self.ids[id_button].text[3:5]),
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

    def close(self):
        self.dialog.dismiss()
        self.dialog = None

    def fechar_dialog(self):
        global id_button
        # Id do botão de bloquear por hora
        if id_button == "btn1":
            self.dialog.dismiss()
            self.dialog = None
            save_config_value("conf/config.ini", "STATE", "hora_atual_bloc_switch", "False")
            hora_e_minuto_bloquear = read_config_value("conf/lista_apps_config.ini", f"{section_name}", f"btn1")
            if not self.dialog:
                self.dialog = MDDialog(
                    title = "Aviso!",
                    text = f"O aplicativo {section_name} foi limitado a {hora_e_minuto_bloquear} de uso!",
                    type = "custom",
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            theme_text_color = "Custom",
                            text_color = (0,0,0,1),
                            on_release=lambda x: self.close()
                        ),
                    ],
                )
            self.dialog.open()

        elif id_button == "btn2" or id_button == "btn3" or id_button == "btn4" or id_button == "btn5" or id_button == "btn6" or id_button == "btn7" or id_button == "btn8" or id_button == "btn9":
            self.dialog.dismiss()
            self.dialog = None
            save_config_value("conf/config.ini", "STATE", "bloquear_horarios", "False")
            
        else:
            self.dialog.dismiss()
            self.dialog = None
            id_button = None

    
#########################################################################################################










# Content responsável por perguntar o nome do aplicativo e tratar seus dados no backend da classe
#########################################################################################################
class Content_add_app_1(MDBoxLayout):
    global bloqueado_selecionado
    text = ""
    def __init__(self):
        super().__init__()
        threading.Thread(target=self.start_thread).start()
    
    def start_thread(self):
        while MDApp.get_running_app():
            time.sleep(0.1)
            self.add_nome_app()

    def add_url(self, text):
        pass
    
    # ADICIONAR APP A LISTA DE APPS
    @mainthread
    def add_nome_app(self):
        if self.ids.text_field_1.text != "":
            self.text = self.ids.text_field_1.text

        def check(self, texto):
            global switch_check_text, bloqueado_selecionado
            if switch_check_text == True and self.text != "":
                switch_check_text = False
                if sql_sqlite != None:
                    # Adiciona o app e suas informações no banco de dadados como o nome do adm deste app e o nome dos bloqueados controlados por este adm, os bloqueados são separados por "/"
                    obter_bloqueados_ativos()
                    nome_do_pacote = obter_pacote(texto)
                    print(f"APP NOVO: {texto} seu pacote: {nome_do_pacote}")
                    sql_sqlite.execute(f"INSERT INTO listaapps (nome_apps, nome_adm, nome_blo) VALUES ('{texto}', '{user_adm_logado}', '{bloqueado_selecionado}')")
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
                        "{texto}",
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
                    try:
                        # Ativa a primeira opção por padrão ao criar o app
                        save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{texto} 1', 'True')
                        save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{texto} 2', 'False')
                        save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{texto} 3', 'False')
                    except:
                        pass

                    # Atualiza a lista de apps mostrados nesta tela
                    ListaApps(text=texto)
                    self.text = ""
                    self.ids.text_field_1.text = ""
            else:
                pass
        # CHAMA A FUNÇÃO COM O NOME DO APP A SER ADICIONADO
        if self.text != "":
            check(self, self.text)
#########################################################################################################














# Contend de icone uix da opção de mostrar os bloqueados ativos
#########################################################################################################
class ItemsDialog(OneLineAvatarIconListItem):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_widget(IconLeftWidget(icon="account"))
        self.text = text
#########################################################################################################






# Tela de configurações da janela que controla a lista de apps
#########################################################################################################
class TelaListaApps(MDScreen):
    icon_btn_switch = False
    switch_loading = False
    carregamento = None
    dialog = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # Função que muda a janela que o usuário está
    def mudar_janela(self, tela):
        MDApp.get_running_app().root.transition = NoTransition()
        MDApp.get_running_app().root.current = tela
    
    # Mostra os bloqueados ativos
    def bloq_info(self):
        if sql_sqlite:
            sql_sqlite.execute("SELECT bloqueados_ativos FROM usuarios_selecionados")
            nome_blo_db = sql_sqlite.fetchall()

            items = []
            for i in nome_blo_db:
                item = ItemsDialog(text=f"{i[0]}")
                item.bind(on_release=lambda x, text=item.text: self.mudar_janela("tela_cadbloqueados"))
                item.bind(on_release=lambda x, text=item.text: dialog.dismiss())
                items.append(item)

            if items:
                dialog = MDDialog(
                    title="Usuários Bloqueados",
                    auto_dismiss=False,
                    type="simple",
                    buttons=[
                        MDFlatButton(
                            text="OK",
                            theme_text_color="Custom",
                            text_color=(0, 0, 0, 1),
                            on_release=lambda x: dialog.dismiss()
                        ),
                    ],
                    items=items,
                )
                dialog.open()
    
    # Função que mostra um Popup na tela ajudando o usuário a compreender sobre o que a tela faz
    def ajuda(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Ajuda",
                type = "custom",
                text = '''Essa tela onde você escolhe um aplicativo que deseja bloquear, ou você mesmo consegue adicionar um aplicativo de sua preferência.\n
Exemplo: basta pesquisar um aplicativo na barra de pesquisa e habilitá-lo, você ainda pode optar por alterar as configurações de bloqueio do aplicativo clicando nos três pontinhos ao adicionar o aplicativo.''',
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
    

    def add_apps(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Adicionar Aplicativo",
                type = "custom",
                content_cls = Content_add_app_1(),
                auto_dismiss = False,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        theme_text_color = "Custom",
                        text_color = (0,0,0,1),
                        on_release=lambda x: self.fechar_dialog_add_app()
                    ),
                ],
            )
        self.dialog.open()

    def fechar_dialog_add_app(self):
        global switch_check_text
        # ESTE SWITCH FAZ COM QUE O APP SEJA ADICIONADO ASSIM QUE O BOTÃO OK FOR PRESSIONADO
        switch_check_text = True
        try:
            self.dialog.dismiss()
        except:
            pass
        self.dialog = None
    
    # Função que retorna uma lista todos os apps que estão no dispositivo
    def get_all_apps_in_device(self):
        if platform == 'android':
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            Intent = autoclass('android.content.Intent')
            package_manager = PythonActivity.mActivity.getPackageManager()
            intent = Intent(Intent.ACTION_MAIN, None)
            intent.addCategory(Intent.CATEGORY_LAUNCHER)
            apps_list = package_manager.queryIntentActivities(intent, 0)
            app_names = [app.loadLabel(package_manager) for app in apps_list]
            return app_names
        else:
            return ['app_1', 'app_2', 'app_3']
    
    # Função que retorna uma lista de todos os apps que não são do sistema
    def list_apps(self):
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

    
    # Função que exclui uma linha especifica do banco de dados sql pelo seu nome
    def excluir_linha_por_nome(nome_a_excluir):
        try:
            # Executar a instrução SQL de exclusão
            sql_sqlite.execute("DELETE FROM listaapps WHERE nome_apl = ?", (nome_a_excluir,))
            sql_sqlite.execute("DELETE FROM aplic_bloc WHERE nome_apl = ?", (nome_a_excluir,))
            # Commit para salvar as alterações
            sqlite_conn.commit()
            print("Linha com o nome '{}' excluída com sucesso.".format(nome_a_excluir))
        except sql_sqlite.Error as e:
            print("Erro ao excluir a linha:", e)

    # Função que muda a janela que o usuário está ao clicar nos três pontos para configurar o aplicativo bloqueado
    def mudar_janela_2(self, tela, text):
        global section_name
        section_name = text
        MDApp.get_running_app().root.transition = NoTransition()
        MDApp.get_running_app().root.current = tela

    
    # Adiciona os apps instalados do dispositivo na lista de apps para bloquear
    def salvar_apps_instalados(self, *args):
        global bloqueado_selecionado, lista_apps_no_dispositivo
        # Checa os apps instalados apenas uma vez
        if read_config_value('conf/config.ini', 'STATE', 'APPS_INSTALADOS_OBTIDOS') == "False":
            save_config_value('conf/config.ini', 'STATE', 'APPS_INSTALADOS_OBTIDOS', 'True')
            obter_bloqueados_ativos()
            if sql_sqlite:
                sql_sqlite.execute("SELECT nome_apps FROM listaapps")
                apps_bd = sql_sqlite.fetchall()
                for nome_do_aplicativo in apps_bd:
                    if nome_do_aplicativo[0] != "CEspreita":
                        nome_do_pacote = obter_pacote(nome_do_aplicativo[0])
                        if nome_do_pacote != "cecotein.informatica.cespreitaapp.informatica":
                            # Atualiza a lista de apps mostrados nesta tela
                            ListaApps(text=nome_do_aplicativo[0])
                            # save_config_value('conf/lista_apps_config.ini', 'CHECKBOXES', f'{nome_do_aplicativo[0]} 1', 'True') # Ativa a primeira opção por padrão ao criar o app
                else:
                    return True
    
    def refresh(self):
        if sql_sqlite:
            sql_sqlite.execute("SELECT nome_apps FROM listaapps")
            apps = sql_sqlite.fetchall()
            for aplicativos in apps:
                self.ids.app_list.clear_widgets()
                ListaApps(text=aplicativos[0])
            self.modify_item()


    # Inicia a thread da tela de carregamento
    def on_pre_enter(self):
        threading.Thread(target=self.start_add_loading).start()
    # Inicia a thread do kivy para adicionar a tela de carregamento
    def start_add_loading(self):
        Clock.schedule_once(self.add_loading)
    # Adiciona a tela de carregamento
    def add_loading(self, *args):
        if self.carregamento == None:
            self.carregamento = Carregamento()
            self.add_widget(self.carregamento)
    # Função para remover a tela de carreamento
    def remove_loading(self):
        if self.carregamento != None:
            self.remove_widget(self.carregamento)
    
    # Função responsável por modificar a cor do texto de um item especifico da lista de apps
    def modify_item(self):
        global item_widgets
        try:
            if sql_sqlite:
                sql_sqlite.execute("SELECT nome_apps FROM listaapps")
                name_apps_list = sql_sqlite.fetchall()
                for app_name in name_apps_list:
                    if read_config_value("conf/lista_apps_config.ini", "CHECKBOXES", f"{app_name[0]} 1") == "False":
                        item = item_widgets[app_name[0]]
                        item.theme_text_color = "Custom"
                        if MDApp.get_running_app().theme_cls.theme_style == 'Light':
                            item.text_color = (0,0,0,1)
                        else:
                            item.text_color = (1,1,1,1)
                    else:
                        item = item_widgets[app_name[0]]
                        item.theme_text_color = "Custom"
                        item.text_color = (1,0,0,1)
        except:
            pass

    def on_enter(self):
        if self.salvar_apps_instalados() == True: # Inicia a função que mostra os apps a serem bloqueados ou administrados
            # Remove a tela de carregamento quando todos os apps forem mostrados
            self.remove_loading()
        self.modify_item()

    def pesquisar(self):
        self.search_item(self.ids.text_field_search.text)

    # NOVO Salva o estado dos switchs externamente
    def update_configs(self):
        MDApp.get_running_app().root.transition = SlideTransition()
        MDApp.get_running_app().root.transition.direction = "down"
        MDApp.get_running_app().root.current = "tela_principal"

    # Função criada para filtragem de pesquisa
    def search_item(self, text=""):
         # Limpe a lista de aplicativos atual
        self.ids.app_list.clear_widgets()
        # Obtenha a entrada de texto da barra de pesquisa
        search_text = text.lower()
        # Preencha a lista apenas com aplicativos que contenham o texto de pesquisa
        for app in self.list_apps():
            if search_text in app.lower():
                ListaApps(text=app)
#########################################################################################################