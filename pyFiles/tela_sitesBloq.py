from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.app import MDApp
from kivy.uix.screenmanager import NoTransition, SlideTransition
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget
from kivy.clock import mainthread
import configparser
import threading
import time
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, cast

lista_sites = [] # Lista que armazena os sites a serem bloqueados
switch_states = {}  # Dicionário para armazenar os estados dos MDSwitches
select_sites = {} # Lista que armazena os sites a serem bloqueados que estão selecionados
sites_deletados = [] # Lista que armazena os sites a serem deletados
lista_sites_mostrados = [] # Lista que armazena os sites que ja estão sendo mostrados ao usuário, assim não repetindo os mesmos sites

id_button = None # Variavel de controle para o id de um botão, não mexer
section_name = None # Variavel de controle para indicar a seção a ser modificada no arquivo config.ini, não mexer

# Variaveis que executam comandos sql
sql_postgre    = None
sql_sqlite     = None

# Variaveis que configuram o sql
postgre_conn   = None
sqlite_conn    = None

# Variavel para controle de execução do código
switch_check_text = False


user_adm_logado = None


# Função para salvar ou atualizar o valor de uma variável em um arquivo de configuração
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


# Função criada para remover uma sessão inteira dos arquivos .ini
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





# Classe de cada item que será criado na lista, exemplo: o item "aplicativo 1", "aplicativo 2" etc
class ListaSites(MDCard):
    icon_btn_switch = False
    def __init__(self, text, switch_state=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elevation = 4
        self.shadow_offset = (0, -8)
        self.shadow_softness = 4
        # Cria um float layout
        float_layout = MDFloatLayout(size = self.size,
                                     pos_hint = {'center_x': 0.5, 'center_y':0.5})
        self.add_widget(float_layout)
        self.ids.float_layout = float_layout

        # Cria um label em cada item da lista para identificar este item
        label = MDLabel(text="Texto Padrão",
                        theme_text_color = "Custom",
                        text_color = (1,1,1,1),
                        pos_hint = {'center_x': 0.55, 'center_y':0.5})  # Crie uma instância de MDLabel
        float_layout.add_widget(label)  # Adicione o MDLabel ao MDCard
        self.ids.label = label  # Defina uma referência ao MDLabel
        # Cria um botão com um icone de lixeira para excluir um item da lista
        icon_button_delete = MDIconButton(icon = 'trash-can-outline',
                                   pos_hint = {'center_x': 0.8, 'center_y':0.5},
                                   theme_icon_color = "Custom",
                                   icon_color = (1,0,0,1),
                                   ripple_alpha = 0,
                                   on_release = lambda x:self.delete())
        float_layout.add_widget(icon_button_delete)
        self.ids.icon_button = icon_button_delete
        # Cria um botão para levar o usuário para as configurações do item selecionado
        icon_button_dots = MDIconButton(icon = 'dots-vertical',
                                        pos_hint = {'center_x': 0.9, 'center_y':0.5},
                                        theme_icon_color = "Custom",
                                        icon_color = (1,1,1,1),
                                        on_release = lambda x: self.mudar_janela('sites_config'))
        float_layout.add_widget(icon_button_dots)
        self.ids.icon_button_dots = icon_button_dots
        self.modify_color_item_theme()

    def modify_color_item_theme(self):
        if MDApp.get_running_app().theme_cls.theme_style == 'Light':
            self.ids.label.text_color = (0,0,0,1)
            self.md_bg_color = (0.9, 0.9, 0.9, 1)
            self.ids.float_layout.md_bg_color = (0.9, 0.9, 0.9, 1)
            self.ids.icon_button_dots.icon_color = (0, 0, 0, 1)
        else:
            self.ids.label.text_color = (1,1,1,1)
            self.md_bg_color = (0.3,0.3,0.3,1)
            self.ids.float_layout.md_bg_color = (0.3,0.3,0.3,1)
            self.ids.icon_button_dots.icon_color = (1, 1, 1, 1)

    # Função que muda a janela que o usuário está ao clicar nos três pontos para configurar o aplicativo bloqueado
    def mudar_janela(self, tela):
        global section_name
        print(f"[ + ] Configurações do {self.ids.label.text}")
        section_name = self.ids.label.text
        MDApp.get_running_app().root.transition = NoTransition()
        MDApp.get_running_app().root.current = tela
    # Salva os estados dos swites fora do programa para que ao ser executado novamente seus estados não sejam perdidos
    def save_switch_states(self):
        for i in lista_sites:
            save_config_value("conf/lista_sites_config.ini", "SWITCH STATES", f"{i}", f"{switch_states.get(i)}")
    # FUNÇÃO RESPONSAVEL POR DELETAR OS ITENS DA LISTA PRINCIPAL ONDE MOSTRAM APENAS ITENS SELECIONADOS PELO USUÁRIO
    def delete(self):
        global lista_site, sites_deletados
        TelaSites_Bloq().update_switch_state(self.icon_btn_switch, self.ids.label.text)
        self.save_switch_states()
        self.parent.remove_widget(self)
        lista_sites.remove(f'{self.ids.label.text}')
        sites_deletados.append(f'{self.ids.label.text}')
        for i in sites_deletados:
            try:
                save_config_value("conf/lista_sites_config.ini", "SITES_REMOVIDOS", f"{i}", "None")
                del select_sites[f'{i}']
                sql_sqlite.execute("DELETE FROM listasites WHERE nome_sites = ?", (i,))
                sqlite_conn.commit()
            except:
                pass






class Content(MDBoxLayout):
    def __init__(self, text1, text2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.text_field_1.text = f'{text1}'
        self.ids.text_field_2.text = f'{text2}'

    def limit_value(self, text_field, max_value):
        global id_button, section_name
        if id_button != None and id_button == "btn1":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn1.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn1", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn2":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn2.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn2", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn3":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn3.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn3", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn4":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn4.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn4", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn5":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn5.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn5", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn6":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn6.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn6", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn7":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn7.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn7", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn8":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn8.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn8", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        
        if id_button != None and id_button == "btn9":
            # Define o ultimo valor salvo para o Textfield
            MDApp.get_running_app().root.get_screen('sites_config').ids.btn9.text = f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}"
            # Salva o ultimo valor modificado do Textfield
            save_config_value("conf/lista_sites_config.ini", f"{section_name}", "btn9", f"{self.ids.text_field_1.text}:{self.ids.text_field_2.text}")
        try:
            # Faz o controle de erros para impossibilitar que o usuário ultrapasse as horas reais ou coloque horas inexistentes
            value = int(text_field.text)
            if value > max_value:
                text_field.text = str(max_value)
            if len(text_field.text) > 2:
                text_field.text = str("")
        except ValueError:
            text_field.text = ''











# Tela de configurações do item atual
class TelaSites_config(MDScreen):
    dialog = None
    check_1 = False
    check_2 = False
    check_3 = False
    # Função que controla o grupo de checkbox, para que ao selecionar um os outros se desativam e vice e versa
    def checkbox_group(self, checkbox):
        cont = 0
        checkboxes = [self.ids.check_1, self.ids.check_2, self.ids.check_3]
        for i in lista_sites:
            if section_name in i:
                for cb in checkboxes:
                    cont = cont + 1
                    if cb == checkbox:
                        cb.active = True
                        save_config_value("conf/lista_sites_config.ini", "CHECKBOXES", f"{section_name} {cont}", "True")
                    else:
                        cb.active = False
                        save_config_value("conf/lista_sites_config.ini", "CHECKBOXES", f"{section_name} {cont}", "False")
    
    # Função padrão do kivy para executar uma ação ao entrar em uma tela
    def on_pre_enter(self, *args):
        self.update_buttons_states(section_name)
        self.get_checkbox_state()
    # Função responsavel por checar os estados dos checkboxes para que ao executar novamente o programa seus ultimos estados ainda estejam salvos
    def get_checkbox_state(self):
        for i in lista_sites:
            if section_name in i:
                for cont in range(1, 4):
                    checkbox = read_config_value("conf/lista_sites_config.ini", "CHECKBOXES", f"{section_name} {cont}")
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
    # Função responsavel por retornar a janela anterior
    def voltar(self):
        MDApp.get_running_app().root.transition.direction = "right"
        MDApp.get_running_app().root.current = "sites_bloqueados"

    # Função responsavel por atualizar os estados de todos os botões da janela
    def update_buttons_states(self, section):
        for i in lista_sites:
            if section in i:
                btn1 = read_config_value("conf/lista_sites_config.ini", section, f"btn1")
                btn2 = read_config_value("conf/lista_sites_config.ini", section, f"btn2")
                btn3 = read_config_value("conf/lista_sites_config.ini", section, f"btn3")
                btn4 = read_config_value("conf/lista_sites_config.ini", section, f"btn4")
                btn5 = read_config_value("conf/lista_sites_config.ini", section, f"btn5")
                btn6 = read_config_value("conf/lista_sites_config.ini", section, f"btn6")
                btn7 = read_config_value("conf/lista_sites_config.ini", section, f"btn7")
                btn8 = read_config_value("conf/lista_sites_config.ini", section, f"btn8")
                btn9 = read_config_value("conf/lista_sites_config.ini", section, f"btn9")

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
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn1", f"09:00")
                    btn1 = read_config_value("conf/lista_sites_config.ini", section, f"btn1")
                    self.ids.btn1.text = f"{btn1}"
                if btn2 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn2", f"07:00")
                    btn2 = read_config_value("conf/lista_sites_config.ini", section, f"btn2")
                    self.ids.btn2.text = f"{btn2}"
                if btn3 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn3", f"08:00")
                    btn3 = read_config_value("conf/lista_sites_config.ini", section, f"btn3")
                    self.ids.btn3.text = f"{btn3}"
                if btn4 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn4", f"09:00")
                    btn4 = read_config_value("conf/lista_sites_config.ini", section, f"btn4")
                    self.ids.btn4.text = f"{btn4}"
                if btn5 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn5", f"10:00")
                    btn5 = read_config_value("conf/lista_sites_config.ini", section, f"btn5")
                    self.ids.btn5.text = f"{btn5}"
                if btn6 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn6", f"11:00")
                    btn6 = read_config_value("conf/lista_sites_config.ini", section, f"btn6")
                    self.ids.btn6.text = f"{btn6}"
                if btn7 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn7", f"12:00")
                    btn7 = read_config_value("conf/lista_sites_config.ini", section, f"btn7")
                    self.ids.btn7.text = f"{btn7}"
                if btn8 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn8", f"13:00")
                    btn8 = read_config_value("conf/lista_sites_config.ini", section, f"btn8")
                    self.ids.btn8.text = f"{btn8}"
                if btn9 == None:
                    save_config_value("conf/lista_sites_config.ini", f"{section}", "btn9", f"14:00")
                    btn9 = read_config_value("conf/lista_sites_config.ini", section, f"btn9")
                    self.ids.btn9.text = f"{btn9}"

    # Função que cria um Popup para selecionar os valores dos horários
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
    # Função responsavel por fechar o Popup
    def fechar_dialog(self):
        global id_button
        self.dialog.dismiss()
        self.dialog = None
        id_button = None











class Content_add_site(MDBoxLayout):
    nome_site = None
    text = ""
    def __init__(self):
        super().__init__()
        threading.Thread(target=self.start_thread).start()
    # Theading criado para adicionar o site ao banco de dados, checar suas informações e fazer o tratamento de dados
    def start_thread(self):
        while MDApp.get_running_app():
            time.sleep(0.1)
            self.add_nome_site()
    
    @mainthread
    def add_nome_site(self):
        if self.ids.text_field_2.text != "" and self.ids.text_field_1 != "":
            self.text = self.ids.text_field_2.text
            self.url = self.ids.text_field_1.text

        def check(self, texto, url):
            global switch_check_text, select_sites
            if switch_check_text == True:
                if self.text != "":
                    try:
                        sql_sqlite.execute(f"INSERT INTO listasites (nome_sites, url_sites) VALUES ('{texto}', '{url}')") # Adiciona o site no banco de dados sql
                        sqlite_conn.commit()
                        # Se o site adicionado for o mesmo que ja foi excluido alguma vez, ele tira ele da lista de excluidos e adiciona novamente
                        remover_item_ini('conf/lista_sites_config.ini', 'SITES_REMOVIDOS', f'{texto}')
                        TelaSites_Bloq().obter_dados() # Atualiza a lista
                        switch_state = switch_states[texto]
                        card = ListaSites(text=texto, switch_state=switch_state)
                        card.ids.label.text = f"{texto}"
                        MDApp.get_running_app().root.get_screen("sites_bloqueados").ids.content.add_widget(card)

                        select_sites[f'{texto}'] = f"{url}"

                        # Ativa a primeira opção por padrão ao criar o site
                        save_config_value('conf/lista_sites_config.ini', 'CHECKBOXES', f'{texto} 1', 'True')
                        save_config_value('conf/lista_sites_config.ini', 'CHECKBOXES', f'{texto} 2', 'False')
                        save_config_value('conf/lista_sites_config.ini', 'CHECKBOXES', f'{texto} 3', 'False')
                        
                        self.ids.text_field_2.text = ""
                        self.text = ""
                        self.ids.text_field_1.text = ""
                        self.url = ""
                        switch_check_text = False
                    except:
                        pass
            else:
                pass
        if self.text != "":
            check(self, self.text, self.url)








# Classe que armazena os widgets da lista de sites
class ItemsDialog(OneLineAvatarIconListItem):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_widget(IconLeftWidget(icon="account"))
        self.text = text

# Tela de configurações da janela que controla a lista de sites
class TelaSites_Bloq(MDScreen):
    global lista_sites
    dialog = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        threading.Thread(target=self.block_website_start_thread).start()
    
    def block_website_start_thread(self):
        while MDApp.get_running_app():
            time.sleep(0.5)
            self.block_website()
    
    # Função que bloqueia o site
    def block_website(self):
        global select_sites
        for sites in lista_sites:
            for chave in select_sites:
                url = select_sites[f"{chave}"]
                if read_config_value("conf/lista_sites_config.ini", "CHECKBOXES", f"{chave} 1") == "True":
                    print(f"o site: '{chave}' com a url: '{url}' está bloqueado")

                    if platform == 'android':
                        # Obtém a classe WebViewClient do Java
                        WebViewClient = autoclass('cecotein.informatica.cespreitaapp.informatica.MyWebViewClient')

                        # Cria uma instância de ArrayList para os sites bloqueados
                        ArrayList = autoclass('java.util.ArrayList')
                        java_blocked_sites = ArrayList()

                        # Adiciona os sites bloqueados à lista
                        java_blocked_sites.add(url)

                        # Cria uma instância de MyWebViewClient com a lista de sites bloqueados
                        web_view_client = WebViewClient(cast('java.util.ArrayList', java_blocked_sites))

                        # Chama o método para definir o cliente WebView personalizado
                        self.set_webview_client(web_view_client)
    
    def set_webview_client(self, web_view_client):
        if platform == 'android':
            # Chama o método Java para definir o cliente WebView personalizado
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.setWebViewClient(web_view_client)
        
    # Função que muda a janela que o usuário está
    def mudar_janela(self, tela):
        MDApp.get_running_app().root.transition = NoTransition()
        MDApp.get_running_app().root.current = tela
    
    def user_bloq_info(self):
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
                text = '''Aqui é a tela onde você escolhe um site que deseja bloquear, ou você mesmo consegue adicionar um site de sua preferência.\n
Exemplo: basta pesquisar um site na barra de pesquisa e habilitá-lo, você ainda pode optar por alterar as configurações de bloqueio do site clicando nos três pontinhos ao adicionar o site.''',
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

    # Função que inicia um Popup para adicionar o site
    def add_site(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title = "Adicionar Site",
                type = "custom",
                content_cls = Content_add_site(),
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
        global switch_check_text
        switch_check_text = True
        self.dialog.dismiss()
        self.dialog = None


    # Função do próprio kivy que é executada ao entrar na janela
    def on_pre_enter(self):
        for i in lista_sites:
            if i in switch_states:
                new_value = read_config_value("conf/lista_sites_config.ini", "SWITCH STATES", f"{i}")
                if new_value == "True":
                    switch_states[i] = True
                if new_value == "False":
                    switch_states[i] = False
        self.ids.content.clear_widgets()
        self.search_item("")

    # Função responsavel pela pesquisa dos itens
    def pesquisar(self):
        self.ids.content.clear_widgets()
        self.search_item(self.ids.text_field_search.text)

    # OBTEM INFORMAÇÕES DE VARIAVEIS E DADOS SALVOS NOS BANCO DE DADOS E SAVA NAS VARIÁVEIS
    def obter_dados(self, *args):
        global select_sites
        try:
            if sql_sqlite != None:
                sql_sqlite.execute("SELECT nome_sites FROM listasites")
                resultados = sql_sqlite.fetchall()
                for linha in resultados:
                    sites = linha[0]  # A coluna está no índice 0
                    if sites not in lista_sites:
                        lista_sites.append(sites)

                    if sites not in select_sites:
                        select_sites[f"{sites}"] = "None"
            
                        sql_sqlite.execute("SELECT url_sites FROM listasites")
                        resultados = sql_sqlite.fetchall()
                        for linha in resultados:
                            url = linha[0]  # A coluna está no índice 0
                            if url not in select_sites.get(sites, "None"):
                                select_sites[sites] = url

            for i in lista_sites:
                self.update_switch_state(False, i)
        except Exception as e:
            print(e)
    
    # Função responsavel por obter o texto da pesquisa
    def get_text(self, text):
        if len(text) == 0:
            self.ids.content.clear_widgets()
            self.search_item("")

    # NOVO Salva o estado dos switchs externamente
    def update_configs(self):
        MDApp.get_running_app().root.transition = SlideTransition()
        MDApp.get_running_app().root.transition.direction = "down"
        MDApp.get_running_app().root.current = "tela_principal"
        for i in lista_sites:
            save_config_value("conf/lista_sites_config.ini", "SWITCH STATES", f"{i}", f"{switch_states.get(i)}")

    # Função que deleta itens ja excluidos ou inválidos da pesquisa
    def deletar_items_indesejados(self):
        config = configparser.ConfigParser()
        config.read('conf/lista_sites_config.ini')
        # Obtenha todos os itens da seção "Seção1"
        secao = 'SITES_REMOVIDOS'
        itens = config.items(secao)
        # Itere sobre os itens e imprima as chaves e valores
        for chave, valor in itens:
            if chave in lista_sites:
                lista_sites.remove(f'{chave}')

    # Função criada para filtragem de pesquisa e controle de dados da pesquisa
    def search_item(self, text=""):
        self.deletar_items_indesejados()
        self.ids.content.clear_widgets()
        try:
            text = text.lower()  # Converter o texto de pesquisa para minúsculas
            self.ids.content.clear_widgets()
            for i in lista_sites:
                switch_state = switch_states[i]
                card = ListaSites(text=i, switch_state=switch_state)
                card.ids.label.text = f"{i}"
                if text in i.lower():  # Converter o texto do item para minúsculas antes de comparar
                    self.ids.content.add_widget(card)
        except Exception as e:
            print(e)

    # Salva o estado do switch para que ao pesquisar um novo item, seu estado(ativado ou desativado) ainda esteja salvo
    def update_switch_state(self, value, text):
        switch_states[text] = value